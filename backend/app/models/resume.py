from dataclasses import dataclass


@dataclass
class ExperienceEntry:
    title: str
    company: str
    period: str
    description: str


@dataclass
class ResumeAnalysis:
    summary: str
    skills: list[str]
    experience: list[ExperienceEntry]
    suggestions: list[str]
