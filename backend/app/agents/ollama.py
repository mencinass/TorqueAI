from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatGenerationError(RuntimeError):
    """Raised when the local chat provider cannot produce a response."""


class OllamaChatProvider:
    """Generate chat responses through Ollama's HTTP API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.CHAT_MODEL
        self.timeout = timeout if timeout is not None else settings.CHAT_TIMEOUT
        self.temperature = temperature if temperature is not None else settings.CHAT_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else settings.CHAT_MAX_TOKENS
        self._client = client

    async def generate(self, messages: List[Dict[str, str]]) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        try:
            if self._client is not None:
                response = await self._client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(f"{self.base_url}/api/chat", json=payload)
                    response.raise_for_status()
                    data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ChatGenerationError("Ollama chat generation failed") from exc

        content = data.get("message", {}).get("content") if isinstance(data, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ChatGenerationError("Ollama returned an invalid chat response")
        return content.strip()


def get_chat_provider() -> Optional[OllamaChatProvider]:
    """Return the configured provider, or None for extractive mode."""
    provider = settings.CHAT_PROVIDER.lower()
    if provider == "extractive":
        return None
    if provider == "ollama":
        return OllamaChatProvider()
    if provider == "nvidia":
        return NvidiaChatProvider()
    raise ValueError(f"Unknown CHAT_PROVIDER={provider!r}. Valid options: ollama, nvidia, extractive")


class _SlidingWindowRateLimiter:
    """Cap calls to at most *max_calls* within a rolling *period* seconds.

    Shared across provider instances so the whole process respects one
    account-wide rate limit (e.g. NVIDIA's "up to 40 rpm" tier).
    """

    def __init__(self, max_calls: int, period: float = 60.0) -> None:
        self._max_calls = max_calls
        self._period = period
        self._timestamps: Deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                while self._timestamps and now - self._timestamps[0] >= self._period:
                    self._timestamps.popleft()
                if len(self._timestamps) < self._max_calls:
                    self._timestamps.append(now)
                    return
                wait_for = self._period - (now - self._timestamps[0])
                logger.debug("nvidia_rate_limit_wait", extra={"wait_seconds": round(wait_for, 2)})
                await asyncio.sleep(max(wait_for, 0.05))


class NvidiaChatProvider:
    """Generate chat responses through NVIDIA's OpenAI-compatible NIM API.

    A shared, module-level rate limiter enforces the account's requests-per-
    minute quota (default 40 rpm) across every instance in this process.
    """

    _rate_limiter: Optional[_SlidingWindowRateLimiter] = None

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.api_key = api_key or settings.NVIDIA_API_KEY
        if not self.api_key:
            raise ChatGenerationError("NVIDIA_API_KEY is not configured")
        self.base_url = (base_url or settings.NVIDIA_BASE_URL).rstrip("/")
        self.model = model or settings.NVIDIA_CHAT_MODEL
        self.timeout = timeout if timeout is not None else settings.CHAT_TIMEOUT
        self.temperature = temperature if temperature is not None else settings.CHAT_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else settings.CHAT_MAX_TOKENS
        self._client = client
        if NvidiaChatProvider._rate_limiter is None:
            NvidiaChatProvider._rate_limiter = _SlidingWindowRateLimiter(settings.NVIDIA_RATE_LIMIT_RPM)

    async def generate(self, messages: List[Dict[str, str]]) -> str:
        assert NvidiaChatProvider._rate_limiter is not None
        await NvidiaChatProvider._rate_limiter.acquire()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        try:
            if self._client is not None:
                response = await self._client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ChatGenerationError("NVIDIA chat generation failed") from exc

        choices = data.get("choices") if isinstance(data, dict) else None
        content = choices[0]["message"]["content"] if choices else None
        if not isinstance(content, str) or not content.strip():
            raise ChatGenerationError("NVIDIA returned an invalid chat response")
        return content.strip()
