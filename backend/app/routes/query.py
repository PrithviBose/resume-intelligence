from fastapi import APIRouter

from app.controllers.query_controller import query_resume
from app.schemas.query import QueryRequest, QueryResult

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResult)
def query(request: QueryRequest) -> QueryResult:
    return query_resume(request)
