from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


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
    raise ValueError(f"Unknown CHAT_PROVIDER={provider!r}. Valid options: ollama, extractive")
