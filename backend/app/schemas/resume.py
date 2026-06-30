from pydantic import BaseModel


class ExperienceItem(BaseModel):
    title: str
    company: str
    period: str
    description: str


class AnalysisResult(BaseModel):
    summary: str
    skills: list[str]
    experience: list[ExperienceItem]
    suggestions: list[str]
