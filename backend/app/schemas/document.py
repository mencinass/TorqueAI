from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["MINI Cooper R56 Repair Manual"])
    file_path: str = Field(..., min_length=1, max_length=500, examples=["service_guide/MINI_R56/mini_R56_service.pdf"])
    file_size_bytes: int = Field(default=0, ge=0, examples=[588153153])
    document_type: str = Field(default="workshop_manual", max_length=50, examples=["workshop_manual"])
    system: str = Field(default="general", max_length=50, examples=["steering"])
    language: str = Field(default="en", max_length=10, examples=["en"])
    generation_id: Optional[int] = Field(None, examples=[1])
    engine_id: Optional[int] = Field(None, examples=[1])


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    generation_code: Optional[str] = None
    engine_code: Optional[str] = None

