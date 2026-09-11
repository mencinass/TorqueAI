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


@pytest.mark.asyncio
async def test_chat_is_grounded_and_cites_manual_source():
    service = ChatService(qdrant=FakeQdrant(), embeddings=MockEmbeddingProvider(dim=8))
    response = await service.answer(
        ChatRequest(question="Como acessar a caixa de direcao?", generation_code="R56", system="steering")
    )
    assert response.grounded is True
    assert "Remova a protecao" in response.answer
    assert response.citations[0].page_number == 142


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
async def test_chat_page_is_available(async_client: httpx.AsyncClient):
    response = await async_client.get("/api/v1/chat/")
    assert response.status_code == 200
    assert "TorqueAI" in response.text
    assert "Consulta técnica" in response.text


@pytest.mark.asyncio
async def test_chat_returns_503_when_ollama_is_unavailable(async_client: httpx.AsyncClient, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.chat.ChatService.answer",
        AsyncMock(side_effect=ChatGenerationError("internal details")),
    )
    response = await async_client.post(
        "/api/v1/chat/messages",
        json={"question": "Qual o procedimento?"},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "O servico de busca dos manuais esta indisponivel no momento."
