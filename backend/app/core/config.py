"""Application configuration loaded from environment variables.

Uses pydantic-settings so every value is typed, validated, and documented in
one place. Import the singleton ``settings`` everywhere instead of reading
``os.environ`` directly — this keeps configuration access testable and explicit.
"""
from __future__ import annotations

from functools import lru_cache
import json
from typing import List, Literal, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # ---- App ----
    APP_NAME: str = "TalentTrail"
    ENVIRONMENT: Literal["development", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173"]

    # ---- Security ----
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # ---- Database ----
    DATABASE_URL: str = "sqlite:///./talenttrail.db"

    # ---- LLM provider selection ----
    LLM_PROVIDER: Literal["azure", "ollama"] = "azure"
    # Disable TLS verification for LLM/embeddings calls ONLY on a dev machine
    # behind a corporate proxy that performs SSL interception (otherwise every
    # Azure call fails with APIConnectionError and agents silently fall back to
    # baseline content). Keep True in production / Docker.
    LLM_VERIFY_SSL: bool = True

    # ---- Azure OpenAI ----
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o-mini"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = ""

    # ---- Ollama ----
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "llama3"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # ---- Vector store ----
    CHROMA_PERSIST_DIR: str = "./.chroma"

    # ---- File storage ----
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 10

    # ---- Live job sources ----
    # When true, the discovery agent fetches real, live postings from public
    # job APIs (Remotive, Arbeitnow, Jobicy). When false, deterministic mock
    # postings are used (useful for offline tests/demos).
    USE_LIVE_JOBS: bool = True
    # Disable TLS verification ONLY for local dev behind a corporate proxy that
    # performs SSL interception. Keep True in production / Docker.
    JOB_API_VERIFY_SSL: bool = True
    JOB_API_TIMEOUT: int = 20
    # SerpApi (https://serpapi.com) Google Jobs engine. When a key is set, the
    # discovery agent prefers real Google Jobs results (full JDs, India-aware)
    # and falls back to the free public APIs if SerpApi is unavailable.
    SERPAPI_KEY: str = ""
    # Default location applied when the user does not specify one (e.g. "India").
    DEFAULT_JOB_LOCATION: str = "India"

    # ---- Observability ----
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "talenttrail"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):
        # Accept JSON list string, comma-separated string, or plain string.
        # pydantic-settings v2 passes raw strings for Union types without
        # attempting json.loads first, so we handle all formats here.
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except (json.JSONDecodeError, ValueError):
                    pass
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _coerce_debug(cls, v):
        # Some shells/tooling export DEBUG values like "release" or "development".
        # Treat truthy/falsey strings normally and map known non-boolean modes
        # to a sensible default so local startup doesn't fail unexpectedly.
        if isinstance(v, str):
            lowered = v.strip().lower()
            if lowered in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if lowered in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return v

    @property
    def is_azure(self) -> bool:
        return self.LLM_PROVIDER == "azure"


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the .env file is parsed only once per process."""
    return Settings()


settings = get_settings()
