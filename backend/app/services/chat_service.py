from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agents.ollama import OllamaChatProvider, get_chat_provider
from app.agents.prompt import build_grounded_messages
from app.core.config import settings
from app.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.rag.qdrant_manager import QdrantManager
from app.schemas.chat import ChatCitation, ChatHistoryResponse, ChatMessage, ChatRequest, ChatResponse


class ChatService:
    """Retrieval-first chat service with an in-memory session history."""

    NO_EVIDENCE = (
        "Nao encontrei evidencia suficiente nos manuais indexados para responder "
        "com seguranca. Informe o veiculo, geracao ou sistema e tente novamente."
    )
    _sessions: Dict[str, List[ChatMessage]] = {}

    def __init__(
        self,
        qdrant: Optional[QdrantManager] = None,
        embeddings: Optional[BaseEmbeddingProvider] = None,
        chat_provider: Optional[OllamaChatProvider] = None,
    ) -> None:
        self.qdrant = qdrant or QdrantManager()
        self.embeddings = embeddings or get_embedding_provider()
        self.chat_provider = chat_provider if chat_provider is not None else get_chat_provider()

    async def answer(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())
        query_vector = (await self.embeddings.embed([request.question]))[0]
        results = await self.qdrant.search_chunks(
            query_vector,
            generation_code=request.generation_code,
            system=request.system,
            limit=request.top_k,
        )
        supported_results = [
            result
            for result in results
            if self._payload(result).get("text")
            and float(getattr(result, "score", 0.0)) >= settings.CHAT_MIN_SCORE
        ]
        citations = [self._citation(result) for result in supported_results]
        history = [
            {"role": message.role, "content": message.content}
            for message in self._sessions.get(session_id, [])
        ]
        answer = await self._compose_answer(
            request.question,
            supported_results,
            citations,
            history,
        )
        now = datetime.now(timezone.utc)
        user_message = ChatMessage(role="user", content=request.question, created_at=now)
        assistant_message = ChatMessage(
            role="assistant",
            content=answer,
            citations=citations,
            created_at=now,
        )
        self._sessions.setdefault(session_id, []).extend([user_message, assistant_message])
        return ChatResponse(
            session_id=session_id,
            answer=answer,
            grounded=bool(citations),
            citations=citations,
            message=assistant_message,
        )

    def history(self, session_id: str) -> ChatHistoryResponse:
        return ChatHistoryResponse(
            session_id=session_id,
            messages=self._sessions.get(session_id, []),
        )

    async def _compose_answer(
        self,
        question: str,
        results: List[Any],
        citations: List[ChatCitation],
        history: List[Dict[str, str]],
    ) -> str:
        if not citations:
            return self.NO_EVIDENCE
        if self.chat_provider is not None:
            messages = build_grounded_messages(question, results, history)
            return await self.chat_provider.generate(messages)
        snippets = []
        for result in results:
            payload = self._payload(result)
            text = str(payload.get("text", "")).strip()
            if text:
                snippets.append(text)
        return "\n\n".join(snippets)

    @staticmethod
    def _payload(result: Any) -> Dict[str, Any]:
        payload = getattr(result, "payload", None)
        return payload if isinstance(payload, dict) else {}

    def _citation(self, result: Any) -> ChatCitation:
        payload = self._payload(result)
        return ChatCitation(
            document_title=str(payload.get("document_title", "Manual tecnico")),
            document_id=int(payload.get("document_id", 0)),
            chapter=str(payload.get("section_title", "Nao informado")),
            page_number=int(payload.get("page_number", 0)),
            section=str(payload.get("system", "general")),
            score=max(float(getattr(result, "score", 0.0)), 0.0),
        )
