"""Centralised LLM + embeddings factory.

Everything that needs an LLM imports from here so the rest of the codebase is
provider-agnostic. Switching between Azure OpenAI and Ollama is a single env
variable (``LLM_PROVIDER``) and never requires touching agent code.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import List

import httpx
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def _http_clients() -> tuple[httpx.Client, httpx.AsyncClient]:
    """Build (sync, async) httpx clients for the Azure/OpenAI SDK.

    When ``LLM_VERIFY_SSL`` is False we disable TLS verification so calls work
    behind a corporate SSL-intercepting proxy. Cached so we reuse connections.
    """
    verify = settings.LLM_VERIFY_SSL
    if not verify:
        logger.warning("llm.ssl_verify_disabled")
    return httpx.Client(verify=verify), httpx.AsyncClient(verify=verify)


@lru_cache
def get_chat_model(temperature: float = 0.2) -> BaseChatModel:
    """Return a configured chat model for the active provider.

    Temperature defaults low because most agents perform extraction/scoring
    where determinism matters more than creativity. Creative agents (cover
    letters) request a higher temperature explicitly.
    """
    if settings.is_azure:
        from langchain_openai import AzureChatOpenAI

        sync_client, async_client = _http_clients()
        logger.info("llm.init", provider="azure", deployment=settings.AZURE_OPENAI_DEPLOYMENT)
        return AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            temperature=temperature,
            timeout=60,
            max_retries=2,
            http_client=sync_client,
            http_async_client=async_client,
        )

    from langchain_community.chat_models import ChatOllama

    logger.info("llm.init", provider="ollama", model=settings.OLLAMA_CHAT_MODEL)
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_CHAT_MODEL,
        temperature=temperature,
    )


class _HashingEmbeddings(Embeddings):
    """Deterministic, dependency-free fallback embedder.

    Used when no real embedding deployment is configured so the app still runs
    end-to-end in demos/tests. Produces stable 256-dim vectors from token
    hashing — good enough for relative cosine ranking, not for production.
    """

    DIM = 256

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.DIM
        for token in text.lower().split():
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            vec[h % self.DIM] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


class _ResilientEmbeddings(Embeddings):
    """Wrap a real embeddings provider with a deterministic fallback.

    Behind corporate SSL-intercepting proxies the real provider can fail at
    runtime (e.g. tiktoken cannot download its BPE file, or the embedding
    endpoint is unreachable). Rather than letting that bubble up as a 500, we
    transparently switch to the local hashing embedder. The switch is sticky so
    we never repeatedly pay the cost of a failing network call, and it keeps the
    query/document vectors dimensionally consistent within a request.
    """

    def __init__(self, primary: Embeddings) -> None:
        self._primary = primary
        self._fallback = _HashingEmbeddings()
        self._degraded = False

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self._degraded:
            try:
                return self._primary.embed_documents(texts)
            except Exception as exc:  # noqa: BLE001
                logger.warning("embeddings.fallback", error=str(exc))
                self._degraded = True
        return self._fallback.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        if not self._degraded:
            try:
                return self._primary.embed_query(text)
            except Exception as exc:  # noqa: BLE001
                logger.warning("embeddings.fallback", error=str(exc))
                self._degraded = True
        return self._fallback.embed_query(text)


@lru_cache
def get_embeddings() -> Embeddings:
    """Return an embeddings client, falling back to a local hashing embedder."""
    if settings.is_azure and settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
        from langchain_openai import AzureOpenAIEmbeddings

        sync_client, async_client = _http_clients()
        logger.info("embeddings.init", provider="azure")
        return _ResilientEmbeddings(
            AzureOpenAIEmbeddings(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                http_client=sync_client,
                http_async_client=async_client,
                # Avoid tiktoken's network download of the BPE vocabulary, which
                # fails behind SSL-intercepting proxies; count tokens locally.
                tiktoken_enabled=False,
            )
        )

    if not settings.is_azure:
        try:
            from langchain_community.embeddings import OllamaEmbeddings

            logger.info("embeddings.init", provider="ollama")
            return _ResilientEmbeddings(
                OllamaEmbeddings(
                    base_url=settings.OLLAMA_BASE_URL,
                    model=settings.OLLAMA_EMBEDDING_MODEL,
                )
            )
        except Exception:  # pragma: no cover - defensive
            pass

    logger.warning("embeddings.init", provider="hashing-fallback")
    return _HashingEmbeddings()
