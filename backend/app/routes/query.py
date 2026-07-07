from fastapi import APIRouter

from app.controllers.query_controller import query_resume, query_resume_agentic
from app.schemas.query import AgentQueryResult, QueryRequest, QueryResult

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResult)
def query(request: QueryRequest) -> QueryResult:
    return query_resume(request)


@router.post("/query/agent", response_model=AgentQueryResult)
def query_agent(request: QueryRequest) -> AgentQueryResult:
    return query_resume_agentic(request)
