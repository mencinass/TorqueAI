from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.vehicle import (
    BrandCreate,
    BrandResponse,
    EngineCreate,
    EngineResponse,
    GenerationCreate,
    GenerationResponse,
    ModelCreate,
    ModelResponse,
    VehicleCreate,
    VehicleDetailResponse,
    VehicleResponse,
)
from app.services.vehicle_service import VehicleService

router = APIRouter()


# ==============================================================================
# Brands
# ==============================================================================
@router.get("/brands", response_model=List[BrandResponse], summary="List all vehicle brands")
async def list_brands(db: AsyncSession = Depends(get_db)):
    return await VehicleService.get_brands(db)


@router.post(
    "/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new vehicle brand",
)
async def create_brand(payload: BrandCreate, db: AsyncSession = Depends(get_db)):
    return await VehicleService.create_brand(db, payload)


# ==============================================================================
# Models
# ==============================================================================
@router.get("/models", response_model=List[ModelResponse], summary="List models (optionally by brand)")
async def list_models(
    brand_id: Optional[int] = Query(None, description="Filter models by Brand ID"),
    db: AsyncSession = Depends(get_db),
):
    return await VehicleService.get_models(db, brand_id=brand_id)


@router.post(
    "/models",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new model for a brand",
)
async def create_model(payload: ModelCreate, db: AsyncSession = Depends(get_db)):
    return await VehicleService.create_model(db, payload)


# ==============================================================================
# Generations
# ==============================================================================
@router.get(
    "/generations",
    response_model=List[GenerationResponse],
    summary="List vehicle generations / chassis codes",
)
async def list_generations(
    model_id: Optional[int] = Query(None, description="Filter by Model ID"),
    code: Optional[str] = Query(None, description="Filter by chassis code (e.g. R56)"),
    db: AsyncSession = Depends(get_db),
):
    return await VehicleService.get_generations(db, model_id=model_id, code=code)


@router.post(
    "/generations",
    response_model=GenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new generation for a model",
)
async def create_generation(payload: GenerationCreate, db: AsyncSession = Depends(get_db)):
    return await VehicleService.create_generation(db, payload)


# ==============================================================================
# Engines
# ==============================================================================
@router.get("/engines", response_model=List[EngineResponse], summary="List engine variants")
async def list_engines(
    code: Optional[str] = Query(None, description="Filter by engine code (e.g. N16)"),
    db: AsyncSession = Depends(get_db),
):
    return await VehicleService.get_engines(db, code=code)


@router.post(
    "/engines",
    response_model=EngineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new engine specification",
)
async def create_engine(payload: EngineCreate, db: AsyncSession = Depends(get_db)):
    return await VehicleService.create_engine(db, payload)


# ==============================================================================
# Vehicles
# ==============================================================================
@router.get("/", response_model=List[VehicleResponse], summary="List vehicle configurations")
async def list_vehicles(
    generation_id: Optional[int] = Query(None, description="Filter by Generation ID"),
    engine_id: Optional[int] = Query(None, description="Filter by Engine ID"),
    db: AsyncSession = Depends(get_db),
):
    return await VehicleService.get_vehicles(db, generation_id=generation_id, engine_id=engine_id)


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a vehicle configuration (generation + engine)",
)
async def create_vehicle(payload: VehicleCreate, db: AsyncSession = Depends(get_db)):
    return await VehicleService.create_vehicle(db, payload)


@router.get(
    "/picker",
    summary="Picker options (generations and systems) for the chat UI",
)
async def get_picker_options(db: AsyncSession = Depends(get_db)):
    return await VehicleService.get_picker_options(db)


@router.get(
    "/{vehicle_id}",
    response_model=VehicleDetailResponse,
    summary="Get comprehensive vehicle details by ID",
)
async def get_vehicle_detail(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    vehicle = await VehicleService.get_vehicle_detail(db, vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle configuration with ID {vehicle_id} not found",
        )
    return vehicle

