from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.parse import SearchHitSchema


class QueryRequest(BaseModel):
    resume_id: str
    query: str = Field(min_length=1, max_length=500)
    user_name: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)


class QueryUnderstanding(BaseModel):
    """Step 1 output: how to search the resume."""

    search_query: str
    intent: Literal["factual", "jd_fit", "summary", "other"]


class QueryEvidence(BaseModel):
    """Step 2 output: facts extracted from retrieved chunks."""

    key_facts: list[str]
    matches: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    jd_fit: Literal["strong", "partial", "weak", "unknown"] | None = None
    insufficient_context: bool = False


class QueryChainTrace(BaseModel):
    """Intermediate outputs from each prompt-chain step."""

    step1_understanding: QueryUnderstanding
    retrieval_chunk_count: int
    step2_evidence: QueryEvidence


class QueryResult(BaseModel):
    resume_id: str
    query: str
    answer: str
    sources: list[SearchHitSchema]
    chain: QueryChainTrace


class AgentToolCall(BaseModel):
    """One tool call the agent decided to make, whichever tool it was."""

    tool_name: str
    arguments: dict
    result_summary: str


class AgentQueryResult(BaseModel):
    resume_id: str
    query: str
    answer: str
    tool_calls: list[AgentToolCall]
