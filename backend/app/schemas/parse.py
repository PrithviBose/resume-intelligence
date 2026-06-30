from pydantic import BaseModel, Field

from app.schemas.user import UserProfileSchema


class TextChunkSchema(BaseModel):
    index: int
    text: str
    start_char: int
    end_char: int


class EmbeddingInfo(BaseModel):
    resume_id: str
    model_name: str
    embedding_dimension: int


class ParseResult(BaseModel):
    filename: str
    file_type: str
    text_length: int
    full_text: str
    chunk_count: int
    chunks: list[TextChunkSchema]
    embedding: EmbeddingInfo
    user: UserProfileSchema


class SearchRequest(BaseModel):
    resume_id: str
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)


class SearchHitSchema(BaseModel):
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    score: float


class SearchResult(BaseModel):
    resume_id: str
    query: str
    results: list[SearchHitSchema]
