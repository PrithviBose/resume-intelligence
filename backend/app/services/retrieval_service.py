import uuid
from dataclasses import dataclass

from app.lib.chroma_client import get_collection
from app.lib.logger import get_logger, log_event
from app.models.embedding import StoredResume
from app.services.chunking_service import TextChunk
from app.services.embedding_service import embed_query

logger = get_logger(__name__)


@dataclass
class SearchHit:
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    score: float


class ChromaEmbeddingStore:
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
        collection = get_collection()

        collection.add(
            ids=[f"{resume_id}_{chunk.index}" for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "resume_id": resume_id,
                    "chunk_index": chunk.index,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "filename": filename,
                    "model_name": model_name,
                    "embedding_dimension": embedding_dimension,
                }
                for chunk in chunks
            ],
        )

        log_event(
            logger,
            "chroma.saved",
            resume_id=resume_id,
            filename=filename,
            chunk_count=len(chunks),
            collection=collection.name,
        )
        return resume_id

    def get(self, resume_id: str) -> StoredResume | None:
        collection = get_collection()
        result = collection.get(
            where={"resume_id": resume_id},
            limit=1,
            include=["metadatas"],
        )

        if not result["ids"]:
            return None

        metadata = result["metadatas"][0]
        return StoredResume(
            resume_id=resume_id,
            filename=str(metadata.get("filename", "")),
            model_name=str(metadata.get("model_name", "")),
            embedding_dimension=int(metadata.get("embedding_dimension", 0)),
            chunks=[],
        )

    def search(self, resume_id: str, query: str, top_k: int = 3) -> list[SearchHit]:
        if self.get(resume_id) is None:
            return []

        collection = get_collection()
        query_vector = embed_query(query)
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where={"resume_id": resume_id},
            include=["documents", "metadatas", "distances"],
        )

        hits: list[SearchHit] = []
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for document, metadata, distance in zip(
            documents, metadatas, distances, strict=True
        ):
            hits.append(
                SearchHit(
                    chunk_index=int(metadata["chunk_index"]),
                    text=document,
                    start_char=int(metadata["start_char"]),
                    end_char=int(metadata["end_char"]),
                    score=round(1 - distance, 4),
                )
            )

        return hits


embedding_store = ChromaEmbeddingStore()
