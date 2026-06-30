import logging
import time

from fastapi import HTTPException

from app.lib.logger import get_logger, log_event
from app.schemas.parse import SearchHitSchema, SearchRequest, SearchResult
from app.services.retrieval_service import embedding_store

logger = get_logger(__name__)


def search_resume(request: SearchRequest) -> SearchResult:
    start = time.perf_counter()

    log_event(
        logger,
        "search.started",
        resume_id=request.resume_id,
        query=request.query,
        top_k=request.top_k,
    )

    resume = embedding_store.get(request.resume_id)
    if resume is None:
        log_event(
            logger,
            "search.failed",
            level=logging.WARNING,
            resume_id=request.resume_id,
            reason="resume_not_found",
        )
        raise HTTPException(status_code=404, detail="Resume embeddings not found")

    hits = embedding_store.search(
        resume_id=request.resume_id,
        query=request.query,
        top_k=request.top_k,
    )

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    log_event(
        logger,
        "search.completed",
        resume_id=request.resume_id,
        query=request.query,
        top_k=request.top_k,
        result_count=len(hits),
        duration_ms=duration_ms,
    )

    return SearchResult(
        resume_id=request.resume_id,
        query=request.query,
        results=[
            SearchHitSchema(
                chunk_index=hit.chunk_index,
                text=hit.text,
                start_char=hit.start_char,
                end_char=hit.end_char,
                score=round(hit.score, 4),
            )
            for hit in hits
        ],
    )
