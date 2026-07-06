import json

from pydantic import BaseModel

from app.lib.azure_openai import get_azure_openai_client
from app.lib.config import settings
from app.lib.logger import get_logger, log_event
from app.schemas.query import QueryEvidence, QueryUnderstanding
from app.schemas.user import UserProfileExtraction

logger = get_logger(__name__)

SYSTEM_PROMPT = """You extract structured profile information from resume text.
Return JSON with these fields:
- user_name: full name of the candidate
- email: email address if present
- current_company: most recent or current employer
- years_of_experience: total years of professional experience as a number

Use null for any field that cannot be determined from the resume."""


def _chat_text(system: str, user: str) -> str:
    client = get_azure_openai_client()
    response = client.chat.completions.create(
        model=settings.azure_openai_deployment_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("LLM returned an empty response")
    return content.strip()


def _chat_json(system: str, user: str, model: type[BaseModel]) -> BaseModel:
    client = get_azure_openai_client()
    schema = model.model_json_schema()

    try:
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": model.__name__,
                    "schema": schema,
                    "strict": True,
                },
            },
        )
    except Exception:
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user + "\n\nRespond with JSON only."},
            ],
            response_format={"type": "json_object"},
        )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("LLM returned an empty response")
    return model.model_validate(json.loads(content))


def extract_user_profile(resume_text: str) -> UserProfileExtraction:
    log_event(
        logger,
        "llm.extraction.started",
        deployment=settings.azure_openai_deployment_name,
        text_length=len(resume_text),
    )

    profile = _chat_json(
        SYSTEM_PROMPT,
        resume_text,
        UserProfileExtraction,
    )

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


# --- Prompt chain: Step 1 — understand the question and build a search query ---

UNDERSTAND_QUERY_PROMPT = """You prepare resume search queries from user questions.
Return JSON with:
- search_query: a concise phrase optimized for semantic search over resume text (skills, roles, companies, education)
- intent: one of factual, jd_fit, summary, other

Use jd_fit when the user asks about role fit, suitability, or comparison to a job description.
Use factual for specific facts (email, skills, years, companies).
Use summary for broad overview requests."""


def understand_query(
    query: str,
    *,
    job_description: str | None = None,
) -> QueryUnderstanding:
    jd = (job_description or "").strip()
    user_parts = [f"User question:\n{query}"]
    if jd:
        user_parts.append(f"Job description:\n{jd}")

    log_event(logger, "llm.chain.step1.started", query_length=len(query), has_jd=bool(jd))

    understanding = _chat_json(
        UNDERSTAND_QUERY_PROMPT,
        "\n\n".join(user_parts),
        QueryUnderstanding,
    )

    if not understanding.search_query.strip():
        understanding = QueryUnderstanding(search_query=query, intent=understanding.intent)

    log_event(
        logger,
        "llm.chain.step1.completed",
        intent=understanding.intent,
        search_query_length=len(understanding.search_query),
    )
    return understanding


# --- Prompt chain: Step 2 — extract evidence from retrieved chunks ---

ANALYZE_EVIDENCE_PROMPT = """You extract evidence from resume excerpts to answer a user question.
Use ONLY the provided excerpts. Do not invent facts.

Return JSON with:
- key_facts: list of relevant facts from the excerpts
- matches: JD requirements the excerpts support (empty if no JD)
- gaps: JD requirements not supported by the excerpts (empty if no JD or unknown)
- jd_fit: strong, partial, weak, or unknown — only when a JD is provided; otherwise null
- insufficient_context: true if excerpts do not contain enough to answer"""


def analyze_evidence(
    query: str,
    hits: list[str],
    *,
    user_name: str | None = None,
    job_description: str | None = None,
) -> QueryEvidence:
    candidate_label = user_name or "the candidate"
    jd = (job_description or "").strip()

    if hits:
        context = "\n\n---\n\n".join(
            f"[Excerpt {index + 1}]\n{text}" for index, text in enumerate(hits)
        )
        excerpt_block = f"Resume excerpts:\n{context}"
    else:
        excerpt_block = "No resume excerpts were retrieved."

    user_parts = [
        f"Candidate: {candidate_label}",
        excerpt_block,
        f"User question:\n{query}",
    ]
    if jd:
        user_parts.insert(1, f"Job description:\n{jd}")

    log_event(
        logger,
        "llm.chain.step2.started",
        source_count=len(hits),
        has_jd=bool(jd),
    )

    evidence = _chat_json(
        ANALYZE_EVIDENCE_PROMPT,
        "\n\n".join(user_parts),
        QueryEvidence,
    )

    log_event(
        logger,
        "llm.chain.step2.completed",
        fact_count=len(evidence.key_facts),
        match_count=len(evidence.matches),
        gap_count=len(evidence.gaps),
        jd_fit=evidence.jd_fit,
    )
    return evidence


# --- Prompt chain: Step 3 — write the final answer from structured evidence ---

SYNTHESIZE_ANSWER_PROMPT = """You write the final answer to a user's question about a candidate's resume.
Use ONLY the structured evidence provided. Do not add facts that are not in the evidence.
Be concise, factual, and write in complete sentences.
If insufficient_context is true, say you do not have enough information from the resume."""


def synthesize_answer(
    query: str,
    evidence: QueryEvidence,
    *,
    user_name: str | None = None,
) -> str:
    candidate_label = user_name or "the candidate"

    log_event(logger, "llm.chain.step3.started", insufficient=evidence.insufficient_context)

    answer = _chat_text(
        SYNTHESIZE_ANSWER_PROMPT,
        (
            f"Candidate: {candidate_label}\n\n"
            f"User question:\n{query}\n\n"
            f"Structured evidence:\n{evidence.model_dump_json(indent=2)}"
        ),
    )

    log_event(logger, "llm.chain.step3.completed", answer_length=len(answer))
    return answer


def run_query_chain(
    query: str,
    hits: list[str],
    *,
    user_name: str | None = None,
    job_description: str | None = None,
) -> tuple[QueryEvidence, str]:
    """Chain steps 2–3 after retrieval (step 1 runs in the controller)."""
    evidence = analyze_evidence(
        query,
        hits,
        user_name=user_name,
        job_description=job_description,
    )
    answer = synthesize_answer(query, evidence, user_name=user_name)
    return evidence, answer
