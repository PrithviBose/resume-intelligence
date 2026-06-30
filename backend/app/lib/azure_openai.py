from openai import AzureOpenAI

from app.lib.config import settings

_client: AzureOpenAI | None = None


def get_azure_openai_client() -> AzureOpenAI:
    global _client

    if (
        not settings.azure_openai_endpoint
        or not settings.azure_openai_api_key
        or not settings.azure_openai_deployment_name
    ):
        raise RuntimeError(
            "Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT_NAME in backend/.env"
        )

    if _client is None:
        _client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )

    return _client
