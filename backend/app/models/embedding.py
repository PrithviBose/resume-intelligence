from dataclasses import dataclass


@dataclass
class StoredChunk:
    index: int
    text: str
    start_char: int
    end_char: int
    embedding: list[float]


@dataclass
class StoredResume:
    resume_id: str
    filename: str
    model_name: str
    embedding_dimension: int
    chunks: list[StoredChunk]
