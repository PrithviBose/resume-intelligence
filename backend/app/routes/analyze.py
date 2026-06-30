from fastapi import APIRouter, File, UploadFile

from app.controllers.analyze_controller import analyze_resume
from app.schemas.resume import AnalysisResult

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(file: UploadFile = File(...)) -> AnalysisResult:
    return await analyze_resume(file)
