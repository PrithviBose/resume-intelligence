from fastapi import APIRouter, File, UploadFile

from app.controllers.parse_controller import parse_resume
from app.schemas.parse import ParseResult

router = APIRouter(prefix="/api", tags=["parse"])


@router.post("/parse", response_model=ParseResult)
async def parse(file: UploadFile = File(...)) -> ParseResult:
    return await parse_resume(file)
