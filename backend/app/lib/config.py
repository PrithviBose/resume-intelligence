import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class Settings:
    api_title: str = "Resume Intelligence API"
    api_description: str = (
        "Analyze resumes and extract skills, experience, and suggestions"
    )
    api_version: str = "0.1.0"
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_intelligence",
    )
    max_upload_size_bytes: int = int(
        float(os.getenv("MAX_UPLOAD_SIZE_MB", "5")) * 1024 * 1024
    )
    chunk_size: int = 1000
    chunk_overlap: int = 150
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str | None = os.getenv("LOG_FILE", "logs/app.log")
    log_to_console: bool = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5"
    )
    embedding_query_prefix: str = (
        "Represent this sentence for searching relevant passages: "
    )
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_deployment_name: str = os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", ""
    )
    azure_openai_api_version: str = os.getenv(
        "AZURE_OPENAI_API_VERSION", "2025-04-01-preview"
    )
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8001"))
    chroma_collection_name: str = os.getenv(
        "CHROMA_COLLECTION_NAME", "knowledge-base"
    )
    chroma_tenant: str = os.getenv("CHROMA_TENANT", "default_tenant")
    chroma_database: str = os.getenv("CHROMA_DATABASE", "default_database")
    job_description: str = os.getenv("JOB_DESCRIPTION", "")


settings = Settings()
