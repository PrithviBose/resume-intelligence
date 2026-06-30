import json

from app.lib.azure_openai import get_azure_openai_client
from app.lib.config import settings
from app.lib.logger import get_logger, log_event
from app.schemas.user import UserProfileExtraction

logger = get_logger(__name__)

SYSTEM_PROMPT = """You extract structured profile information from resume text.
Return JSON with these fields:
- user_name: full name of the candidate
- email: email address if present
- current_company: most recent or current employer
- years_of_experience: total years of professional experience as a number

Use null for any field that cannot be determined from the resume."""


def extract_user_profile(resume_text: str) -> UserProfileExtraction:
    client = get_azure_openai_client()
    schema = UserProfileExtraction.model_json_schema()

    log_event(
        logger,
        "llm.extraction.started",
        deployment=settings.azure_openai_deployment_name,
        text_length=len(resume_text),
    )

    try:
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": resume_text},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "user_profile",
                    "schema": schema,
                    "strict": True,
                },
            },
        )
    except Exception:
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Extract profile fields from this resume and respond with JSON only:\n\n"
                        f"{resume_text}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("LLM returned an empty response")

    profile = UserProfileExtraction.model_validate(json.loads(content))

    log_event(
        logger,
        "llm.extraction.completed",
        deployment=settings.azure_openai_deployment_name,
        has_name=profile.user_name is not None,
        has_email=profile.email is not None,
        has_company=profile.current_company is not None,
        has_experience=profile.years_of_experience is not None,
    )

    return profile
