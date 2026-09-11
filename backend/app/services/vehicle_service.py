from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.document import TechnicalDocument
from app.models.vehicle import Brand, Engine, Generation, Model, Vehicle
from app.schemas.vehicle import (
    BrandCreate,
    EngineCreate,
    GenerationCreate,
    ModelCreate,
    VehicleCreate,
    VehicleDetailResponse,
)


class VehicleService:
    """Async service managing vehicle catalog persistence and queries."""

    # --------------------------------------------------------------------------
    # Brands
    # --------------------------------------------------------------------------
    @staticmethod
    async def get_brands(db: AsyncSession) -> List[Brand]:
        result = await db.execute(select(Brand).order_by(Brand.name))
        return list(result.scalars().all())

    @staticmethod
    async def create_brand(db: AsyncSession, payload: BrandCreate) -> Brand:
        brand = Brand(name=payload.name, country=payload.country)
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
        return brand

    # --------------------------------------------------------------------------
    # Models
    # --------------------------------------------------------------------------
    @staticmethod
    async def get_models(db: AsyncSession, brand_id: Optional[int] = None) -> List[Model]:
        stmt = select(Model).order_by(Model.name)
        if brand_id:
            stmt = stmt.where(Model.brand_id == brand_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_model(db: AsyncSession, payload: ModelCreate) -> Model:
        model = Model(name=payload.name, brand_id=payload.brand_id)
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model

    # --------------------------------------------------------------------------
    # Generations
    # --------------------------------------------------------------------------
    @staticmethod
    async def get_generations(
        db: AsyncSession, model_id: Optional[int] = None, code: Optional[str] = None
    ) -> List[Generation]:
        stmt = select(Generation).order_by(Generation.year_start)
        if model_id:
            stmt = stmt.where(Generation.model_id == model_id)
        if code:
            stmt = stmt.where(Generation.code.ilike(code))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_generation(db: AsyncSession, payload: GenerationCreate) -> Generation:
        gen = Generation(
            name=payload.name,
            code=payload.code,
            year_start=payload.year_start,
            year_end=payload.year_end,
            model_id=payload.model_id,
        )
        db.add(gen)
        await db.commit()
        await db.refresh(gen)
        return gen

    # --------------------------------------------------------------------------
    # Engines
    # --------------------------------------------------------------------------
    @staticmethod
    async def get_engines(db: AsyncSession, code: Optional[str] = None) -> List[Engine]:
        stmt = select(Engine).order_by(Engine.code)
        if code:
            stmt = stmt.where(Engine.code.ilike(code))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_engine(db: AsyncSession, payload: EngineCreate) -> Engine:
        engine = Engine(
            code=payload.code,
            displacement_l=payload.displacement_l,
            fuel_type=payload.fuel_type,
            power_hp=payload.power_hp,
            valves=payload.valves,
        )
        db.add(engine)
        await db.commit()
        await db.refresh(engine)
        return engine

    # --------------------------------------------------------------------------
    # Vehicles
    # --------------------------------------------------------------------------
    @staticmethod
    async def get_vehicles(
        db: AsyncSession,
        generation_id: Optional[int] = None,
        engine_id: Optional[int] = None,
    ) -> List[Vehicle]:
        stmt = select(Vehicle)
        if generation_id:
            stmt = stmt.where(Vehicle.generation_id == generation_id)
        if engine_id:
            stmt = stmt.where(Vehicle.engine_id == engine_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_vehicle_detail(db: AsyncSession, vehicle_id: int) -> Optional[VehicleDetailResponse]:
        stmt = (
            select(Vehicle)
            .where(Vehicle.id == vehicle_id)
            .options(
                joinedload(Vehicle.generation).joinedload(Generation.model).joinedload(Model.brand),
                joinedload(Vehicle.engine),
            )
        )
        result = await db.execute(stmt)
        vehicle = result.scalar_one_or_none()
        if not vehicle:
            return None

        return VehicleDetailResponse(
            id=vehicle.id,
            brand=vehicle.generation.model.brand.name,
            model=vehicle.generation.model.name,
            generation=vehicle.generation.code,
            generation_name=vehicle.generation.name,
            year_start=vehicle.generation.year_start,
            year_end=vehicle.generation.year_end,
            engine_code=vehicle.engine.code,
            displacement_l=vehicle.engine.displacement_l,
            fuel_type=vehicle.engine.fuel_type,
            power_hp=vehicle.engine.power_hp,
            transmission=vehicle.transmission,
            trim_level=vehicle.trim_level,
        )

    @staticmethod
    async def create_vehicle(db: AsyncSession, payload: VehicleCreate) -> Vehicle:
        vehicle = Vehicle(
            generation_id=payload.generation_id,
            engine_id=payload.engine_id,
            transmission=payload.transmission,
            trim_level=payload.trim_level,
        )
        db.add(vehicle)
        await db.commit()
        await db.refresh(vehicle)
        return vehicle

    # --------------------------------------------------------------------------
    # Picker options for the chat UI (generations + systems with documents)
    # --------------------------------------------------------------------------
    @staticmethod
    async def get_picker_options(db: AsyncSession) -> dict:
        """Return generations and systems that have catalogs, for UI dropdowns."""
        # Generations that have at least one technical document.
        gen_stmt = (
            select(Generation)
            .join(TechnicalDocument, TechnicalDocument.generation_id == Generation.id)
            .options(joinedload(Generation.model).joinedload(Model.brand))
            .order_by(Generation.code)
            .distinct()
        )
        gen_result = await db.execute(gen_stmt)
        generations = gen_result.unique().scalars().all()
        generation_options = [
            {
                "code": g.code,
                "name": g.name,
                "brand": g.model.brand.name if g.model.brand else "",
                "model": g.model.name,
            }
            for g in generations
        ]

        # Distinct systems across documents.
        sys_stmt = (
            select(TechnicalDocument.system)
            .where(TechnicalDocument.system.isnot(None))
            .distinct()
            .order_by(TechnicalDocument.system)
        )
        sys_result = await db.execute(sys_stmt)
        systems = [row[0] for row in sys_result.all() if row[0]]

        return {"generations": generation_options, "systems": systems}

