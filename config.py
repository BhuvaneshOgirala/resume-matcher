import os

OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_MODEL_ENV = "OPENAI_MODEL"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def get_openai_api_key(provided_key: str | None = None) -> str:
    """Return the explicitly provided key or the configured environment secret."""
    provided = (provided_key or "").strip()
    configured = (os.getenv(OPENAI_API_KEY_ENV) or "").strip()
    return provided or configured


def get_openai_model(model_override: str | None = None) -> str:
    """Return the requested model or the configured model/default."""
    requested = (model_override or "").strip()
    configured = (os.getenv(OPENAI_MODEL_ENV) or "").strip()
    return requested or configured or DEFAULT_OPENAI_MODEL
