from typing import Optional
from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class TechnicalDocument(Base, TimestampMixin):
    """Metadata record for a physical service manual, diagram, or workshop guide."""

    __tablename__ = "technical_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(50), default="workshop_manual", nullable=False, index=True
    )
    system: Mapped[str] = mapped_column(
        String(50), default="general", nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    # Scoped vehicle linkages
    generation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("generations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    engine_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("engines.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    generation: Mapped[Optional["Generation"]] = relationship(
        "Generation", back_populates="documents", lazy="joined"
    )
    engine: Mapped[Optional["Engine"]] = relationship(
        "Engine", back_populates="documents", lazy="joined"
    )

