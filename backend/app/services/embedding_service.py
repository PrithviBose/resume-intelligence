from langfuse import observe
from sentence_transformers import SentenceTransformer

from app.lib.config import settings
from app.lib.logger import get_logger, log_event

logger = get_logger(__name__)

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model_name)
    return _model


def warmup_embedding_model() -> None:
    """Load the embedding model and run one encode so query-time search stays fast."""
    model = _get_model()
    model.encode("warmup", normalize_embeddings=True)
    log_event(
        logger,
        "embeddings.warmup.completed",
        model=settings.embedding_model_name,
        dimension=model.get_sentence_embedding_dimension(),
    )


def embed_documents(texts: list[str]) -> list[list[float]]:
    if not texts:        return []

    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]


@observe(name="embed_query")
def embed_query(query: str) -> list[float]:
    model = _get_model()
    prefixed_query = f"{settings.embedding_query_prefix}{query}"
    vector = model.encode(prefixed_query, normalize_embeddings=True)
    return vector.tolist()


def get_embedding_dimension() -> int:
    return _get_model().get_embedding_dimension()
