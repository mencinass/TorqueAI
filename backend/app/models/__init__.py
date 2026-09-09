"""Database ORM models for vehicles, technical documents, and diagnostics."""

from app.models.document import TechnicalDocument
from app.models.vehicle import Brand, Engine, Generation, Model, Vehicle

__all__ = [
    "Brand",
    "Model",
    "Generation",
    "Engine",
    "Vehicle",
    "TechnicalDocument",
]
