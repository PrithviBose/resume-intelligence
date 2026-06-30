from fastapi import APIRouter

from app.controllers.search_controller import search_resume
from app.schemas.parse import SearchRequest, SearchResult

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResult)
def search(request: SearchRequest) -> SearchResult:
    return search_resume(request)
