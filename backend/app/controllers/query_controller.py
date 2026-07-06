import logging
import time

from fastapi import HTTPException

from app.lib.config import settings
from app.lib.logger import get_logger, log_event
from app.schemas.parse import SearchHitSchema
from app.schemas.query import QueryChainTrace, QueryRequest, QueryResult
from app.services.llm_service import run_query_chain, understand_query
from app.services.retrieval_service import embedding_store

logger = get_logger(__name__)


def query_resume(request: QueryRequest) -> QueryResult:
    start = time.perf_counter()
    jd = settings.job_description or None

    log_event(
        logger,
        "query.started",
        resume_id=request.resume_id,
        query=request.query,
        top_k=request.top_k,
        user_name=request.user_name,
    )

    resume = embedding_store.get(request.resume_id)
    if resume is None:
        log_event(
            logger,
            "query.failed",
            level=logging.WARNING,
            resume_id=request.resume_id,
            reason="resume_not_found",
        )
        raise HTTPException(status_code=404, detail="Resume embeddings not found")

    try:
        # Chain step 1: rewrite question into a search-friendly query
        understanding = understand_query(request.query, job_description=jd)

        # RAG retrieval (not LLM): embed search_query and fetch chunks
        hits = embedding_store.search(
            resume_id=request.resume_id,
            query=understanding.search_query,
            top_k=request.top_k,
        )

        # Chain steps 2–3: analyze evidence, then synthesize answer
        evidence, answer = run_query_chain(
            request.query,
            [hit.text for hit in hits],
            user_name=request.user_name,
            job_description=jd,
        )
    except Exception as exc:
        log_event(
            logger,
            "query.failed",
            level=logging.ERROR,
            resume_id=request.resume_id,
            reason="llm_error",
            error=str(exc),
        )
        raise HTTPException(
            status_code=502,
            detail="Failed to generate an answer",
        ) from exc

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    log_event(
        logger,
        "query.completed",
        resume_id=request.resume_id,
        query=request.query,
        source_count=len(hits),
        duration_ms=duration_ms,
    )

    return QueryResult(
        resume_id=request.resume_id,
        query=request.query,
        answer=answer,
        sources=[
            SearchHitSchema(
                chunk_index=hit.chunk_index,
                text=hit.text,
                start_char=hit.start_char,
                end_char=hit.end_char,
                score=round(hit.score, 4),
            )
            for hit in hits
        ],
        chain=QueryChainTrace(
            step1_understanding=understanding,
            retrieval_chunk_count=len(hits),
            step2_evidence=evidence,
        ),
    )
