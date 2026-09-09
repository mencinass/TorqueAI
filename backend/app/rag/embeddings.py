"""Embedding providers for the automotive RAG pipeline.

All providers implement the :class:`BaseEmbeddingProvider` ABC.
HTTP communication uses :mod:`httpx` exclusively — no native/C SDKs.

Usage::

    provider = get_embedding_provider()
    vectors = await provider.embed(["text one", "text two"])
"""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from typing import List

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseEmbeddingProvider(ABC):
    """Abstract base for all embedding backends."""

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Return one embedding vector per text.

        Args:
            texts: Non-empty list of strings to embed.

        Returns:
            List of float vectors; length matches *texts*.
        """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the produced vectors."""


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Embed text via a locally running Ollama server.

    Sends one ``POST /api/embeddings`` request per text so Ollama can handle
    each prompt independently.  Uses a shared :class:`httpx.AsyncClient` with
    a generous timeout suitable for GPU-backed models.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        dim: int | None = None,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = model or settings.EMBEDDING_MODEL
        self._dim = dim or settings.EMBEDDING_DIM
        self._timeout = timeout

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/embed",
                json={"model": self._model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
            vectors = data.get("embeddings")
            if not isinstance(vectors, list) or len(vectors) != len(texts):
                raise ValueError("Ollama returned an invalid embeddings response")
        logger.debug(
            "ollama_embed",
            extra={
                "model": self._model,
                "texts": len(texts),
                "dim": len(vectors[0]) if vectors else 0,
            },
        )
        return vectors


# ---------------------------------------------------------------------------
# OpenAI-compatible provider (httpx only)
# ---------------------------------------------------------------------------


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Embed text via an OpenAI-compatible HTTP endpoint.

    Pure httpx — no ``openai`` SDK dependency.  Works with the official
    OpenAI API or any compatible proxy.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        dim: int | None = None,
        timeout: float = 60.0,
        batch_size: int = 100,
    ) -> None:
        self._api_key = api_key or settings.OPENAI_API_KEY or ""
        self._base_url = (base_url or settings.EMBEDDING_OPENAI_BASE_URL).rstrip("/")
        self._model = model or settings.EMBEDDING_MODEL
        self._dim = dim or settings.EMBEDDING_DIM
        self._timeout = timeout
        self._batch_size = batch_size

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        vectors: List[List[float]] = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for i in range(0, len(texts), self._batch_size):
                batch = texts[i : i + self._batch_size]
                response = await client.post(
                    f"{self._base_url}/embeddings",
                    headers=headers,
                    json={"input": batch, "model": self._model},
                )
                response.raise_for_status()
                data = response.json()
                # OpenAI returns data sorted by index
                batch_vectors = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
                vectors.extend(batch_vectors)
        logger.debug(
            "openai_embed",
            extra={"model": self._model, "texts": len(texts)},
        )
        return vectors


# ---------------------------------------------------------------------------
# Mock provider (deterministic, no network, for tests)
# ---------------------------------------------------------------------------


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic embedding provider for offline testing.

    Produces normalised unit vectors derived from the SHA-256 hash of the
    input text.  Same text always produces the same vector; no GPU or network
    required.
    """

    def __init__(self, dim: int | None = None) -> None:
        self._dim = dim or settings.EMBEDDING_DIM

    @property
    def dimension(self) -> int:
        return self._dim

    def _hash_to_vector(self, text: str) -> List[float]:
        """Convert text to a deterministic unit vector of length *self._dim*."""
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        # Expand the 32-byte seed to cover *dim* floats using multiple digests
        raw: List[float] = []
        digest = seed
        while len(raw) < self._dim:
            digest = hashlib.sha256(digest).digest()
            for i in range(0, len(digest), 2):
                raw.append(int.from_bytes(digest[i : i + 2], "big") - 32768)
        raw = raw[: self._dim]
        # Normalise to unit length
        magnitude = math.sqrt(sum(v * v for v in raw)) or 1.0
        return [v / magnitude for v in raw]

    async def embed(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_to_vector(t) for t in texts]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type[BaseEmbeddingProvider]] = {
    "ollama": OllamaEmbeddingProvider,
    "openai": OpenAIEmbeddingProvider,
    "mock": MockEmbeddingProvider,
}


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Return the embedding provider configured via ``EMBEDDING_PROVIDER`` env var.

    Valid values: ``ollama``, ``openai``, ``mock`` (default: ``mock``).

    Raises:
        ValueError: If an unknown provider name is configured.
    """
    name = settings.EMBEDDING_PROVIDER.lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown EMBEDDING_PROVIDER={name!r}. "
            f"Valid options: {list(_PROVIDERS)}"
        )
    logger.info("embedding_provider_loaded", extra={"provider": name})
    return cls()
