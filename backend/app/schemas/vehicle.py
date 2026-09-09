from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# Brand Schemas
# ==============================================================================
class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["MINI"])
    country: Optional[str] = Field(None, max_length=100, examples=["United Kingdom"])


class BrandCreate(BrandBase):
    pass


class BrandResponse(BrandBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# Model Schemas
# ==============================================================================
class ModelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Cooper"])
    brand_id: int = Field(..., examples=[1])


class ModelCreate(ModelBase):
    pass


class ModelResponse(ModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# Generation Schemas
# ==============================================================================
class GenerationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Second Generation"])
    code: str = Field(..., min_length=1, max_length=50, examples=["R56"])
    year_start: int = Field(..., ge=1900, le=2100, examples=[2007])
    year_end: Optional[int] = Field(None, ge=1900, le=2100, examples=[2013])
    model_id: int = Field(..., examples=[1])


class GenerationCreate(GenerationBase):
    pass


class GenerationResponse(GenerationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# Engine Schemas
# ==============================================================================
class EngineBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, examples=["N16"])
    displacement_l: Optional[float] = Field(None, gt=0, lt=15, examples=[1.6])
    fuel_type: str = Field(default="petrol", examples=["petrol"])
    power_hp: Optional[int] = Field(None, gt=0, lt=2000, examples=[120])
    valves: Optional[int] = Field(None, gt=0, lt=64, examples=[16])


class EngineCreate(EngineBase):
    pass


class EngineResponse(EngineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# Vehicle Configuration Schemas
# ==============================================================================
class VehicleBase(BaseModel):
    generation_id: int = Field(..., examples=[1])
    engine_id: int = Field(..., examples=[1])
    transmission: str = Field(default="Manual", max_length=100, examples=["Manual 6-speed"])
    trim_level: Optional[str] = Field(None, max_length=100, examples=["Cooper"])


class VehicleCreate(VehicleBase):
    pass


class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class VehicleDetailResponse(BaseModel):
    """Rich vehicle context payload for diagnostic matching and prompt hydration."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str = Field(..., examples=["MINI"])
    model: str = Field(..., examples=["Cooper"])
    generation: str = Field(..., examples=["R56"])
    generation_name: str = Field(..., examples=["Second Generation"])
    year_start: int = Field(..., examples=[2007])
    year_end: Optional[int] = Field(None, examples=[2013])
    engine_code: str = Field(..., examples=["N16"])
    displacement_l: Optional[float] = Field(None, examples=[1.6])
    fuel_type: str = Field(..., examples=["petrol"])
    power_hp: Optional[int] = Field(None, examples=[120])
    transmission: str = Field(..., examples=["Manual 6-speed"])
    trim_level: Optional[str] = Field(None, examples=["Cooper"])

