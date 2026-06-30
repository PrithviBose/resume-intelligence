import uuid
from dataclasses import dataclass

from app.models.embedding import StoredChunk, StoredResume
from app.services.embedding_service import embed_query
from app.services.chunking_service import TextChunk


@dataclass
class SearchHit:
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    score: float


class EmbeddingStore:
    def __init__(self) -> None:
        self._resumes: dict[str, StoredResume] = {}

    def save(
        self,
        *,
        filename: str,
        model_name: str,
        embedding_dimension: int,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> str:
        resume_id = str(uuid.uuid4())
        stored_chunks = [
            StoredChunk(
                index=chunk.index,
                text=chunk.text,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                embedding=embedding,
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        self._resumes[resume_id] = StoredResume(
            resume_id=resume_id,
            filename=filename,
            model_name=model_name,
            embedding_dimension=embedding_dimension,
            chunks=stored_chunks,
        )
        return resume_id

    def get(self, resume_id: str) -> StoredResume | None:
        return self._resumes.get(resume_id)

    def search(self, resume_id: str, query: str, top_k: int = 3) -> list[SearchHit]:
        resume = self._resumes.get(resume_id)
        if resume is None:
            return []

        query_vector = embed_query(query)
        scored_chunks = [
            SearchHit(
                chunk_index=chunk.index,
                text=chunk.text,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                score=_dot_product(query_vector, chunk.embedding),
            )
            for chunk in resume.chunks
        ]
        scored_chunks.sort(key=lambda hit: hit.score, reverse=True)
        return scored_chunks[:top_k]


def _dot_product(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


embedding_store = EmbeddingStore()
