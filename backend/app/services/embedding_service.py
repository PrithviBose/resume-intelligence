from sentence_transformers import SentenceTransformer

from app.lib.config import settings

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model_name)
    return _model


def embed_documents(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]


def embed_query(query: str) -> list[float]:
    model = _get_model()
    prefixed_query = f"{settings.embedding_query_prefix}{query}"
    vector = model.encode(prefixed_query, normalize_embeddings=True)
    return vector.tolist()


def get_embedding_dimension() -> int:
    return _get_model().get_embedding_dimension()
