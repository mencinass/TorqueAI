from types import SimpleNamespace
import json

import httpx
import pytest

from app.agents.ollama import ChatGenerationError, OllamaChatProvider, get_chat_provider
from app.core.config import settings
from app.agents.prompt import SYSTEM_PROMPT, build_grounded_messages
from app.rag.embeddings import MockEmbeddingProvider
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_ollama_provider_sends_grounded_chat_payload():
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = request.read()
        return httpx.Response(200, json={"message": {"content": "Resposta [Fonte 1]."}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaChatProvider(
            base_url="http://ollama",
            model="qwen2.5:7b",
            client=client,
        )
        answer = await provider.generate([{"role": "user", "content": "Pergunta"}])

    assert answer == "Resposta [Fonte 1]."
    payload = json.loads(captured["payload"])
    assert payload["stream"] is False
    assert payload["model"] == "qwen2.5:7b"


@pytest.mark.asyncio
async def test_ollama_provider_rejects_malformed_response():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OllamaChatProvider(client=client)
        with pytest.raises(ChatGenerationError):
            await provider.generate([])


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [httpx.Response(500), httpx.ReadTimeout("timeout")])
async def test_ollama_provider_wraps_http_and_timeout_failures(response):
    async def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(response, Exception):
            raise response
        return response

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OllamaChatProvider(client=client)
        with pytest.raises(ChatGenerationError):
            await provider.generate([])


def test_unknown_chat_provider_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="Unknown CHAT_PROVIDER"):
        get_chat_provider()


def test_grounded_prompt_contains_rules_and_numbered_sources():
    result = SimpleNamespace(
        payload={
            "text": "Use o procedimento da secao.",
            "document_title": "Manual R56",
            "section_title": "Steering",
            "page_number": 12,
            "system": "steering",
        }
    )
    messages = build_grounded_messages("Como fazer?", [result])
    assert messages[0]["content"] == SYSTEM_PROMPT
    assert "[Fonte 1]" in messages[-1]["content"]
    assert "Manual R56" in messages[-1]["content"]
    assert "portugues do Brasil" in messages[0]["content"]


@pytest.mark.asyncio
async def test_chat_service_uses_injected_llm_and_preserves_citations():
    class FakeQdrant:
        async def search_chunks(self, *args, **kwargs):
            return [SimpleNamespace(score=0.9, payload={
                "text": "Aperte conforme o manual.",
                "document_title": "Manual R56",
                "document_id": 1,
                "section_title": "Torque",
                "page_number": 22,
                "system": "engine",
            })]

    class FakeChat:
        async def generate(self, messages):
            assert "[Fonte 1]" in messages[-1]["content"]
            return "O manual orienta o procedimento. [Fonte 1]"

    service = ChatService(
        qdrant=FakeQdrant(),
        embeddings=MockEmbeddingProvider(dim=8),
        chat_provider=FakeChat(),
    )
    response = await service.answer(ChatRequest(question="Qual o torque?"))
    assert response.grounded is True
    assert response.answer.endswith("[Fonte 1]")
    assert response.citations[0].page_number == 22
