from typing import List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class Brand(Base, TimestampMixin):
    """Automotive vehicle manufacturer (e.g., MINI, Fiat, BMW)."""

    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    models: Mapped[List["Model"]] = relationship(
        "Model", back_populates="brand", cascade="all, delete-orphan", lazy="selectin"
    )


class Model(Base, TimestampMixin):
    """Vehicle model belonging to a specific brand (e.g., Cooper, 500)."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="models", lazy="joined")
    generations: Mapped[List["Generation"]] = relationship(
        "Generation", back_populates="model", cascade="all, delete-orphan", lazy="selectin"
    )


class Generation(Base, TimestampMixin):
    """Vehicle generation / chassis code (e.g., R56, R53, 312)."""

    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    year_start: Mapped[int] = mapped_column(Integer, nullable=False)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    model: Mapped["Model"] = relationship("Model", back_populates="generations", lazy="joined")
    vehicles: Mapped[List["Vehicle"]] = relationship(
        "Vehicle", back_populates="generation", cascade="all, delete-orphan", lazy="selectin"
    )
    documents: Mapped[List["TechnicalDocument"]] = relationship(
        "TechnicalDocument", back_populates="generation", cascade="all, delete-orphan", lazy="selectin"
    )


class Engine(Base, TimestampMixin):
    """Engine specification variant (e.g., N16, W11, 1.4 Fire)."""

    __tablename__ = "engines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    displacement_l: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fuel_type: Mapped[str] = mapped_column(String(50), default="petrol", nullable=False)
    power_hp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    valves: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    vehicles: Mapped[List["Vehicle"]] = relationship("Vehicle", back_populates="engine", lazy="selectin")
    documents: Mapped[List["TechnicalDocument"]] = relationship(
        "TechnicalDocument", back_populates="engine", lazy="selectin"
    )


class Vehicle(Base, TimestampMixin):
    """Complete vehicle configuration linking generation, engine, and transmission."""

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    generation_id: Mapped[int] = mapped_column(
        ForeignKey("generations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    engine_id: Mapped[int] = mapped_column(
        ForeignKey("engines.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transmission: Mapped[str] = mapped_column(String(100), default="Manual", nullable=False)
    trim_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    generation: Mapped["Generation"] = relationship("Generation", back_populates="vehicles", lazy="joined")
    engine: Mapped["Engine"] = relationship("Engine", back_populates="vehicles", lazy="joined")

