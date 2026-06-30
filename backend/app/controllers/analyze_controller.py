from fastapi import HTTPException, UploadFile

from app.schemas.resume import AnalysisResult, ExperienceItem
from app.services.resume_service import resume_service


async def analyze_resume(file: UploadFile) -> AnalysisResult:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    analysis = await resume_service.analyze(content, file.filename or "resume.pdf")

    return AnalysisResult(
        summary=analysis.summary,
        skills=analysis.skills,
        experience=[
            ExperienceItem(
                title=entry.title,
                company=entry.company,
                period=entry.period,
                description=entry.description,
            )
            for entry in analysis.experience
        ],
        suggestions=analysis.suggestions,
    )
