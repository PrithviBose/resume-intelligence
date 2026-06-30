from app.models.resume import ExperienceEntry, ResumeAnalysis


class ResumeService:
    async def analyze(self, file_content: bytes, filename: str) -> ResumeAnalysis:
        return ResumeAnalysis(
            summary=(
                "Experienced software engineer with 5+ years building scalable "
                "web applications. Strong background in full-stack development "
                "with a focus on modern JavaScript frameworks and cloud-native "
                "architectures. Demonstrated ability to lead projects from "
                "conception to deployment."
            ),
            skills=["JavaScript", "React", "Node.js", "Python", "SQL", "Git"],
            experience=[
                ExperienceEntry(
                    title="Senior Software Engineer",
                    company="Tech Corp",
                    period="2021 – Present",
                    description=(
                        "Led development of customer-facing dashboard serving 50k+ "
                        "users. Reduced page load times by 40% through performance "
                        "optimization."
                    ),
                ),
                ExperienceEntry(
                    title="Software Engineer",
                    company="Startup Inc",
                    period="2019 – 2021",
                    description=(
                        "Built REST APIs and React frontends for B2B SaaS platform. "
                        "Collaborated with cross-functional teams in an agile "
                        "environment."
                    ),
                ),
            ],
            suggestions=[
                "Add quantifiable metrics to each bullet point (e.g., team size, revenue impact).",
                "Include a dedicated Technical Skills section for better ATS parsing.",
                "Highlight leadership experience more prominently in the summary.",
                "Consider adding relevant certifications or open-source contributions.",
            ],
        )


resume_service = ResumeService()
