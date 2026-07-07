import json
import logging

from langfuse import get_client, observe

from app.lib.azure_openai import get_azure_openai_client
from app.lib.config import settings
from app.lib.database import SessionLocal
from app.lib.logger import get_logger, log_event
from app.services.retrieval_service import embedding_store
from app.services.user_service import get_user_by_resume_id

logger = get_logger(__name__)

AGENT_SYSTEM_PROMPT = """You answer questions about a candidate's resume.
You have two tools:
- `search_resume`: semantic search over the resume text. Use it for anything that requires
  reading the resume's content (skills, projects, experience, education, JD fit, etc.).
- `get_candidate_contact_info`: fetches structured contact details (name, email, current company,
  years of experience) already extracted from the resume. Use it for direct factual lookups
  instead of searching resume text for these fields.

Call whichever tool fits the question, as many times as you need, before answering.
Only state facts returned by a tool. If you still don't have enough evidence, say so plainly
instead of guessing. Reply with plain text (no tool call) once you're ready to answer."""

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_resume",
        "description": "Semantic search over the candidate's resume. Returns the most relevant excerpts.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search phrase: skills, roles, companies, education, etc.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of excerpts to retrieve",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
}

CONTACT_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "get_candidate_contact_info",
        "description": (
            "Fetch the candidate's structured contact info (name, email, current company, "
            "years of experience) that was extracted from their resume on upload and stored "
            "in the database. Prefer this over search_resume for these specific fields."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}

TOOLS = [SEARCH_TOOL, CONTACT_INFO_TOOL]

MAX_ITERATIONS = 5


@observe(name="search_resume", as_type="tool")
def _run_search_resume(resume_id: str, fallback_query: str, args: dict) -> tuple[str, str]:
    search_query = args.get("query", fallback_query)
    top_k = min(max(int(args.get("top_k", 3)), 1), 10)

    hits = embedding_store.search(resume_id=resume_id, query=search_query, top_k=top_k)
    result_text = "\n\n".join(hit.text for hit in hits) or "No matching excerpts found."
    result_summary = f"{len(hits)} chunk(s) found"
    return result_text, result_summary


@observe(name="get_candidate_contact_info", as_type="tool")
def _run_get_candidate_contact_info(resume_id: str) -> tuple[str, str]:
    db = SessionLocal()
    try:
        user = get_user_by_resume_id(db, resume_id)
    finally:
        db.close()

    if user is None:
        return "No structured contact info found for this candidate.", "No record in database"

    result_text = "\n".join(
        [
            f"Name: {user.user_name or 'unknown'}",
            f"Email: {user.email or 'unknown'}",
            f"Current company: {user.current_company or 'unknown'}",
            "Years of experience: "
            + (str(user.years_of_experience) if user.years_of_experience is not None else "unknown"),
        ]
    )
    return result_text, "Fetched structured contact info from Postgres"


@observe(name="agent_query")
def run_agent_query(
    query: str,
    resume_id: str,
    *,
    user_name: str | None = None,
    job_description: str | None = None,
) -> tuple[str, list[dict]]:
    """ReAct-style loop: the LLM decides when/how to call the available tools,
    until it gives a final plain-text answer or MAX_ITERATIONS is reached."""
    client = get_azure_openai_client()
    candidate_label = user_name or "the candidate"

    user_content = f"Candidate: {candidate_label}\nQuestion: {query}"
    if job_description:
        user_content += f"\nJob description:\n{job_description}"

    messages: list[dict] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    tool_calls_trace: list[dict] = []

    log_event(logger, "agent.started", resume_id=resume_id, query=query)

    for iteration in range(MAX_ITERATIONS):
        log_event(logger, "agent.iteration.started", iteration=iteration)

        response = client.chat.completions.create(
            model=settings.azure_openai_deployment_name,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message

        # Rename the auto-traced generation so Langfuse shows what this LLM
        # turn did, not a generic "OpenAI-generation".
        turn = iteration + 1
        generation_name = (
            "agent_final_answer"
            if not message.tool_calls
            else f"agent_decide_tools_{turn}"
        )
        get_client().update_current_generation(name=generation_name)

        if not message.tool_calls:
            answer = message.content or "I don't have enough information to answer that."
            log_event(
                logger,
                "agent.completed",
                iterations=iteration + 1,
                tool_call_count=len(tool_calls_trace),
            )
            return answer, tool_calls_trace

        messages.append(message.model_dump(exclude_none=True))

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # Dispatch: map the tool name the model asked for to the Python
            # function that actually knows how to satisfy it. Add new tools
            # by adding a branch here plus an entry in TOOLS above.
            if tool_name == "search_resume":
                result_text, result_summary = _run_search_resume(resume_id, query, args)
            elif tool_name == "get_candidate_contact_info":
                result_text, result_summary = _run_get_candidate_contact_info(resume_id)
            else:
                result_text = f"Unknown tool requested: {tool_name}"
                result_summary = "Unrecognized tool call"

            tool_calls_trace.append(
                {"tool_name": tool_name, "arguments": args, "result_summary": result_summary}
            )
            log_event(
                logger,
                "agent.tool_call",
                tool_name=tool_name,
                arguments=args,
                result_summary=result_summary,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_text,
                }
            )

    log_event(
        logger,
        "agent.max_iterations_reached",
        level=logging.WARNING,
        resume_id=resume_id,
        query=query,
    )
    return (
        "I wasn't able to find a confident answer within the allowed steps.",
        tool_calls_trace,
    )
