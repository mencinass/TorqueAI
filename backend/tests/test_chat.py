from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from app.rag.embeddings import MockEmbeddingProvider
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService
from app.agents.ollama import ChatGenerationError


class FakeQdrant:
    async def search_chunks(self, vector, generation_code=None, system=None, limit=5):
        assert generation_code == "R56"
        assert system == "steering"
        return [
            SimpleNamespace(
                score=0.91,
                payload={
                    "text": "Remova a protecao antes de acessar a caixa de direcao.",
                    "document_title": "MINI R56 Workshop Manual",
                    "document_id": 7,
                    "section_title": "Steering gear",
                    "page_number": 142,
                    "system": "steering",
                },
            )
        ][:limit]


class FakeGeneralQdrant:
    """Stub for the general mechanics collection."""

    async def search_chunks(self, vector, generation_code=None, system=None, limit=5):
        assert generation_code is None, "general layer must not receive vehicle filters"
        return [
            SimpleNamespace(
                score=0.72,
                payload={
                    "text": "A chave de torque deve ser calibrada periodicamente.",
                    "document_title": "A Biblia do Carro",
                    "document_id": 900,
                    "section_title": "Ferramentas",
                    "page_number": 33,
                    "system": "general_mechanics",
                },
            )
        ][:limit]


@pytest.mark.asyncio
async def test_chat_is_grounded_and_cites_manual_source():
    service = ChatService(
        qdrant=FakeQdrant(),
        general_qdrant=FakeGeneralQdrant(),
        embeddings=MockEmbeddingProvider(dim=8),
    )
    response = await service.answer(
        ChatRequest(question="Como acessar a caixa de direcao?", generation_code="R56", system="steering")
    )
    assert response.grounded is True
    assert "Remova a protecao" in response.answer
    assert response.citations[0].page_number == 142


@pytest.mark.asyncio
async def test_chat_combines_automotive_and_general_layers_sorted_by_score():
    """Both layers are searched, vehicle filters only hit the automotive layer,
    and the combined context is ranked by score (general 0.72 < automotive 0.91)."""

    class LowScoreAutomotive:
        async def search_chunks(self, vector, generation_code=None, system=None, limit=5):
            return [
                SimpleNamespace(
                    score=0.45,
                    payload={
                        "text": "Procedimento do manual do veiculo.",
                        "document_title": "MINI R56 Workshop Manual",
                        "document_id": 7,
                        "section_title": "Steering",
                        "page_number": 100,
                        "system": "steering",
                    },
                )
            ]

    captured = {}

    class RecordingChat:
        async def generate(self, messages):
            captured["content"] = messages[-1]["content"]
            return "Resposta [Fonte 1]."

    service = ChatService(
        qdrant=LowScoreAutomotive(),
        general_qdrant=FakeGeneralQdrant(),
        embeddings=MockEmbeddingProvider(dim=8),
        chat_provider=RecordingChat(),
    )
    response = await service.answer(
        ChatRequest(question="Como usar chave de torque?", generation_code="R56")
    )
    assert response.grounded is True
    titles = [c.document_title for c in response.citations]
    assert titles == ["A Biblia do Carro", "MINI R56 Workshop Manual"]
    # The higher-scoring general source must appear first in the prompt context.
    assert captured["content"].index("A Biblia do Carro") < captured["content"].index(
        "MINI R56 Workshop Manual"
    )


@pytest.mark.asyncio
async def test_chat_returns_no_evidence_when_both_layers_are_empty():
    class EmptyQdrant:
        async def search_chunks(self, *args, **kwargs):
            return []

    service = ChatService(
        qdrant=EmptyQdrant(),
        general_qdrant=EmptyQdrant(),
        embeddings=MockEmbeddingProvider(dim=8),
    )
    response = await service.answer(ChatRequest(question="Qual o torque?"))
    assert response.grounded is False
    assert response.citations == []
    assert "evidencia suficiente" in response.answer


def test_chat_rejects_blank_or_out_of_range_questions():
    with pytest.raises(ValidationError):
        ChatRequest(question="  ")
    with pytest.raises(ValidationError):
        ChatRequest(question="ok", top_k=11)


@pytest.mark.asyncio
async def test_chat_returns_no_evidence_without_results():
    class EmptyQdrant:
        async def search_chunks(self, *args, **kwargs):
            return []

    service = ChatService(qdrant=EmptyQdrant(), embeddings=MockEmbeddingProvider(dim=8))
    response = await service.answer(ChatRequest(question="Qual o torque?"))
    assert response.grounded is False
    assert response.citations == []
    assert "evidencia suficiente" in response.answer


@pytest.mark.asyncio
async def test_chat_page_is_available(auth_client: httpx.AsyncClient):
    response = await auth_client.get("/api/v1/chat/")
    assert response.status_code == 200
    assert "TorqueAI" in response.text
    assert "Consulta técnica" in response.text


@pytest.mark.asyncio
async def test_chat_requires_auth(async_client: httpx.AsyncClient):
    response = await async_client.get("/api/v1/chat/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_returns_503_when_ollama_is_unavailable(auth_client: httpx.AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.chat.ChatService.answer",
        AsyncMock(side_effect=ChatGenerationError("internal details")),
    )
    response = await auth_client.post(
        "/api/v1/chat/messages",
        json={"question": "Qual o procedimento?"},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "O servico de busca dos manuais esta indisponivel no momento."
