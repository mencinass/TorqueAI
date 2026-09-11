import os
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.document import TechnicalDocument
from app.models.vehicle import Brand, Engine, Generation, Model, Vehicle


async def seed_initial_data(db: AsyncSession) -> None:
    """Populate database with initial vehicle models, generations, engines, and manual files."""
    count_result = await db.execute(select(func.count(Brand.id)))
    brand_count = count_result.scalar_one()
    if brand_count > 0:
        logger.info(f"Database already contains {brand_count} brands. Skipping seed.")
        return

    logger.info("Seeding initial automotive catalog and service manuals...")

    # 1. Brands
    mini = Brand(name="MINI", country="United Kingdom")
    fiat = Brand(name="Fiat", country="Italy")
    honda = Brand(name="Honda", country="Japan")
    db.add_all([mini, fiat, honda])
    await db.flush()

    # 2. Models
    cooper = Model(name="Cooper", brand_id=mini.id)
    fiat_500 = Model(name="500", brand_id=fiat.id)
    civic = Model(name="Civic", brand_id=honda.id)
    db.add_all([cooper, fiat_500, civic])
    await db.flush()

    # 3. Generations
    r56 = Generation(
        name="Second Generation (Hatchback)",
        code="R56",
        year_start=2007,
        year_end=2013,
        model_id=cooper.id,
    )
    r53 = Generation(
        name="First Generation (Cooper S)",
        code="R53",
        year_start=2002,
        year_end=2006,
        model_id=cooper.id,
    )
    type_312 = Generation(
        name="Nuova 500 (Type 312)",
        code="312",
        year_start=2007,
        year_end=2014,
        model_id=fiat_500.id,
    )
    civic_eg = Generation(
        name="Fifth Generation (EG/EH)",
        code="EG",
        year_start=1992,
        year_end=1995,
        model_id=civic.id,
    )
    civic_ej = Generation(
        name="Sixth Generation (EJ/EK)",
        code="EJ",
        year_start=1996,
        year_end=2000,
        model_id=civic.id,
    )
    db.add_all([r56, r53, type_312, civic_eg, civic_ej])
    await db.flush()

    # 4. Engines
    n16 = Engine(code="N16", displacement_l=1.6, fuel_type="petrol", power_hp=120, valves=16)
    n14 = Engine(code="N14", displacement_l=1.6, fuel_type="petrol", power_hp=175, valves=16)
    w11 = Engine(code="W11", displacement_l=1.6, fuel_type="petrol", power_hp=163, valves=16)
    fire14 = Engine(code="1.4 Fire", displacement_l=1.4, fuel_type="petrol", power_hp=100, valves=16)
    db.add_all([n16, n14, w11, fire14])
    await db.flush()

    # 5. Vehicle configurations
    v_r56_cooper = Vehicle(
        generation_id=r56.id, engine_id=n16.id, transmission="Manual 6-speed", trim_level="Cooper"
    )
    v_r56_cooper_s = Vehicle(
        generation_id=r56.id, engine_id=n14.id, transmission="Manual 6-speed", trim_level="Cooper S"
    )
    v_r53_cooper_s = Vehicle(
        generation_id=r53.id, engine_id=w11.id, transmission="Manual 6-speed", trim_level="Cooper S"
    )
    v_fiat_500 = Vehicle(
        generation_id=type_312.id, engine_id=fire14.id, transmission="Manual 6-speed", trim_level="Lounge"
    )
    db.add_all([v_r56_cooper, v_r56_cooper_s, v_r53_cooper_s, v_fiat_500])
    await db.flush()

    # 6. Technical Documents (resolving local physical files)
    def resolve_size(relative_path: str) -> int:
        candidates = [
            relative_path,
            os.path.join("..", relative_path),
            os.path.join(os.getcwd(), relative_path),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), relative_path),
        ]
        for p in candidates:
            if os.path.exists(p) and os.path.isfile(p):
                return os.path.getsize(p)
        return 0

    docs = [
        TechnicalDocument(
            title="MINI Cooper R56 Service Manual (2007-2013)",
            file_path="service_guide/MINI_R56/mini_R56_service.pdf",
            file_size_bytes=resolve_size("service_guide/MINI_R56/mini_R56_service.pdf"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=r56.id,
            engine_id=n16.id,
        ),
        TechnicalDocument(
            title="MINI Cooper S R56 Repair Manual",
            file_path="service_guide/MINI_R56/356037748-mini-cooper-s-r56-repair.pdf",
            file_size_bytes=resolve_size("service_guide/MINI_R56/356037748-mini-cooper-s-r56-repair.pdf"),
            document_type="repair_manual",
            system="engine",
            language="en",
            generation_id=r56.id,
            engine_id=n14.id,
        ),
        TechnicalDocument(
            title="MINI Cooper R53 Service Manual (2002-2006)",
            file_path="service_guide/MINI_53/mini_R53_service.pdf",
            file_size_bytes=resolve_size("service_guide/MINI_53/mini_R53_service.pdf"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=r53.id,
            engine_id=w11.id,
        ),
        TechnicalDocument(
            title="Fiat 500 Workshop Manual (2007-2014)",
            file_path="service_guide/Fiat/Fiat 500/fiat-500-2007-2014-workshop-manual.pdf",
            file_size_bytes=resolve_size("service_guide/Fiat/Fiat 500/fiat-500-2007-2014-workshop-manual.pdf"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=type_312.id,
            engine_id=fire14.id,
        ),
        # --- Honda Civic (unique files only; duplicates excluded) ---
        TechnicalDocument(
            title="Honda Civic 1992-1995 Service Manual (USDM)",
            file_path="service_guide/CVIC/USDM_92-95_civic.pdf",
            file_size_bytes=resolve_size("service_guide/CVIC/USDM_92-95_civic.pdf"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=civic_eg.id,
        ),
        TechnicalDocument(
            title="Honda Civic EJ6/EJ7/EJ8 (1996-2000) Service Manual",
            file_path="service_guide/CVIC/Civic EJ6, EJ7, EJ8 (96-00) Service Manual.pdf",
            file_size_bytes=resolve_size("service_guide/CVIC/Civic EJ6, EJ7, EJ8 (96-00) Service Manual.pdf"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=civic_ej.id,
        ),
        TechnicalDocument(
            title="Honda Civic (96-00) — 62SR300A",
            file_path="service_guide/CVIC/62sr300a.pdf",
            file_size_bytes=resolve_size("service_guide/CVIC/62sr300a.pdf"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=civic_ej.id,
        ),
        TechnicalDocument(
            title="Honda Civic (96-00) — 62SR300B",
            file_path="service_guide/CVIC/62SR300B.PDF",
            file_size_bytes=resolve_size("service_guide/CVIC/62SR300B.PDF"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=civic_ej.id,
        ),
        TechnicalDocument(
            title="Honda Civic (96-00) — 62SR320",
            file_path="service_guide/CVIC/62SR320.PDF",
            file_size_bytes=resolve_size("service_guide/CVIC/62SR320.PDF"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=civic_ej.id,
        ),
        TechnicalDocument(
            title="Honda Civic (96-00) — 62SR321",
            file_path="service_guide/CVIC/62sr321.pdf",
            file_size_bytes=resolve_size("service_guide/CVIC/62sr321.pdf"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=civic_ej.id,
        ),
        TechnicalDocument(
            title="Honda Civic (96-00) — 62SR322",
            file_path="service_guide/CVIC/62sr322 (1).pdf",
            file_size_bytes=resolve_size("service_guide/CVIC/62sr322 (1).pdf"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=civic_ej.id,
        ),
        TechnicalDocument(
            title="Honda Civic (96-00) — 62SR323",
            file_path="service_guide/CVIC/62SR323.PDF",
            file_size_bytes=resolve_size("service_guide/CVIC/62SR323.PDF"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=civic_ej.id,
        ),
        TechnicalDocument(
            title="Honda Civic (96-00) — 62SR324",
            file_path="service_guide/CVIC/62sr324 (1).pdf",
            file_size_bytes=resolve_size("service_guide/CVIC/62sr324 (1).pdf"),
            document_type="workshop_manual",
            system="general",
            language="en",
            generation_id=civic_ej.id,
        ),
    ]
    db.add_all(docs)
    await db.commit()
    logger.info("Automotive catalog and initial documents seeded successfully.")

