"""The LLM chosen by the user: a provider, a model and an API key, used through LangChain.

Same approach as MorningDevNews: one function, `get_chat_model()`, works for the four providers.
"""

import os
from pathlib import Path

from dotenv import dotenv_values, set_key
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from sqlmodel import Session

from app.models import LlmSettings

# Supported providers, each with a default model (the user can type another one).
# The keys are LangChain's provider names, passed as they are to init_chat_model().
PROVIDERS = {
    "openai": {"label": "OpenAI", "default_model": "gpt-5-mini", "key_param": "api_key"},
    "anthropic": {"label": "Anthropic (Claude)", "default_model": "claude-haiku-5-5", "key_param": "api_key"},
    "google_genai": {"label": "Google (Gemini)", "default_model": "gemini-3.5-flash-lite", "key_param": "google_api_key"},
    "mistralai": {"label": "Mistral AI", "default_model": "mistral-small-latest", "key_param": "api_key"},
}

# The API key never goes to the database: it stays in a .env file of a local data folder,
# ignored by Git. backend/data/ by default; Docker mounts that same folder (docker-compose.yml).
DATA_DIR = Path(os.environ.get("DATA_DIR") or Path(__file__).resolve().parent.parent / "data")
ENV_PATH = DATA_DIR / ".env"
API_KEY_VAR = "LLM_API_KEY"

# There is only one user, so one settings row: this one, created by a migration.
SETTINGS_ID = 1


class LlmNotConfiguredError(Exception):
    """No provider or no API key saved yet."""


def guess_provider(api_key: str) -> str | None:
    """Guess the provider from the key prefix. Mistral keys have no prefix: None."""
    key = api_key.strip()
    if key.startswith("sk-ant-"):
        return "anthropic"
    if key.startswith("AIza"):
        return "google_genai"
    if key.startswith("sk-"):  # tested after "sk-ant-", which also starts with "sk-"
        return "openai"
    return None


def read_api_key() -> str | None:
    """Read the key from the .env file at each call, so a key saved from the page is used at once."""
    if not ENV_PATH.exists():
        return None
    return dotenv_values(ENV_PATH).get(API_KEY_VAR) or None


def save_api_key(api_key: str) -> None:
    """Write the key to the .env file, creating the folder and the file if needed."""
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PATH.touch(exist_ok=True)
    set_key(ENV_PATH, API_KEY_VAR, api_key)


def get_settings(session: Session) -> LlmSettings:
    return session.get_one(LlmSettings, SETTINGS_ID)


def effective_model(settings: LlmSettings) -> str | None:
    """The model the user typed, or the provider's default one."""
    if settings.model:
        return settings.model
    if settings.provider in PROVIDERS:
        return PROVIDERS[settings.provider]["default_model"]
    return None


def get_chat_model(settings: LlmSettings) -> BaseChatModel:
    """Build the LangChain chat model from the saved settings and the saved key."""
    api_key = read_api_key()
    if settings.provider not in PROVIDERS or not api_key:
        raise LlmNotConfiguredError("Choose a provider and save an API key on the LLM page.")
    key_param = PROVIDERS[settings.provider]["key_param"]
    # Bounded timeout and retries: a wrong model or a quota error fails fast instead of hanging.
    return init_chat_model(
        effective_model(settings),
        model_provider=settings.provider,
        timeout=60,
        max_retries=2,
        **{key_param: api_key},
    )
