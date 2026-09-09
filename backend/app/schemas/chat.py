from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    question: str = Field(..., min_length=3, max_length=2000)
    generation_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    system: Optional[str] = Field(default=None, min_length=1, max_length=100)
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator("generation_code", "system")
    @classmethod
    def normalize_filter(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("question must not be blank")
        return question


class ChatCitation(BaseModel):
    document_title: str
    document_id: int
    chapter: str
    page_number: int
    section: str
    score: float = Field(ge=0)


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    citations: List[ChatCitation] = Field(default_factory=list)
    created_at: datetime


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    grounded: bool
    citations: List[ChatCitation] = Field(default_factory=list)
    message: ChatMessage


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatMessage]
