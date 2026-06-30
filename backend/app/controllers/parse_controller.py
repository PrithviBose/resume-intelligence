import logging
import time

from fastapi import HTTPException, UploadFile

from app.lib.config import settings
from app.lib.database import SessionLocal
from app.lib.logger import get_logger, log_event
from app.lib.text_parser import ALLOWED_EXTENSIONS, extract_text, get_file_type
from app.schemas.parse import EmbeddingInfo, ParseResult, TextChunkSchema
from app.services.chunking_service import chunk_text
from app.services.embedding_service import (
    embed_documents,
    get_embedding_dimension,
)
from app.services.llm_service import extract_user_profile
from app.services.retrieval_service import embedding_store
from app.services.user_service import create_user

logger = get_logger(__name__)


async def parse_resume(file: UploadFile) -> ParseResult:
    start = time.perf_counter()
    filename = file.filename or "upload"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    log_event(
        logger,
        "parse.started",
        filename=filename,
        extension=extension,
        content_type=file.content_type,
    )

    if f".{extension}" not in ALLOWED_EXTENSIONS:
        log_event(
            logger,
            "parse.failed",
            level=logging.WARNING,
            filename=filename,
            reason="unsupported_file_type",
            extension=extension,
        )
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported",
        )

    content = await file.read()
    file_size_bytes = len(content)

    if not content:
        log_event(
            logger,
            "parse.failed",
            level=logging.WARNING,
            filename=filename,
            reason="empty_file",
        )
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if file_size_bytes > settings.max_upload_size_bytes:
        log_event(
            logger,
            "parse.failed",
            level=logging.WARNING,
            filename=filename,
            reason="file_too_large",
            file_size_bytes=file_size_bytes,
            max_upload_size_bytes=settings.max_upload_size_bytes,
        )
        raise HTTPException(status_code=400, detail="File exceeds 5 MB limit")

    try:
        full_text = extract_text(content, filename)
        file_type = get_file_type(filename)
    except ValueError as exc:
        log_event(
            logger,
            "parse.failed",
            level=logging.WARNING,
            filename=filename,
            reason="extraction_error",
            error=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not full_text.strip():
        log_event(
            logger,
            "parse.failed",
            level=logging.WARNING,
            filename=filename,
            file_type=file_type,
            reason="no_text_extracted",
            file_size_bytes=file_size_bytes,
        )
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from the file",
        )

    chunks = chunk_text(
        full_text,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )

    embed_start = time.perf_counter()
    chunk_texts = [chunk.text for chunk in chunks]
    embeddings = embed_documents(chunk_texts)
    embedding_dimension = get_embedding_dimension()
    resume_id = embedding_store.save(
        filename=filename,
        model_name=settings.embedding_model_name,
        embedding_dimension=embedding_dimension,
        chunks=chunks,
        embeddings=embeddings,
    )
    embed_duration_ms = round((time.perf_counter() - embed_start) * 1000, 2)

    llm_start = time.perf_counter()
    try:
        profile = extract_user_profile(full_text)
    except RuntimeError as exc:
        log_event(
            logger,
            "parse.failed",
            level=logging.ERROR,
            filename=filename,
            reason="llm_not_configured",
            error=str(exc),
        )
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        log_event(
            logger,
            "parse.failed",
            level=logging.ERROR,
            filename=filename,
            reason="llm_extraction_error",
            error=str(exc),
        )
        raise HTTPException(
            status_code=502,
            detail="Failed to extract profile from resume",
        ) from exc
    llm_duration_ms = round((time.perf_counter() - llm_start) * 1000, 2)

    db = SessionLocal()
    try:
        user = create_user(
            db,
            profile,
            resume_id=resume_id,
            source_filename=filename,
        )
    except ValueError as exc:
        log_event(
            logger,
            "parse.failed",
            level=logging.WARNING,
            filename=filename,
            reason="duplicate_email",
            email=profile.email,
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        log_event(
            logger,
            "parse.failed",
            level=logging.ERROR,
            filename=filename,
            reason="database_error",
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to save user profile",
        ) from exc
    finally:
        db.close()

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    log_event(
        logger,
        "parse.completed",
        filename=filename,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        text_length=len(full_text),
        chunk_count=len(chunks),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        resume_id=resume_id,
        user_id=user.id,
        embedding_model=settings.embedding_model_name,
        embedding_dimension=embedding_dimension,
        embed_duration_ms=embed_duration_ms,
        llm_duration_ms=llm_duration_ms,
        duration_ms=duration_ms,
    )

    return ParseResult(
        filename=filename,
        file_type=file_type,
        text_length=len(full_text),
        full_text=full_text,
        chunk_count=len(chunks),
        chunks=[
            TextChunkSchema(
                index=chunk.index,
                text=chunk.text,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
            )
            for chunk in chunks
        ],
        embedding=EmbeddingInfo(
            resume_id=resume_id,
            model_name=settings.embedding_model_name,
            embedding_dimension=embedding_dimension,
        ),
        user=user,
    )
