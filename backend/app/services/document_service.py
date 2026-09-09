from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.document import TechnicalDocument
from app.models.vehicle import Generation
from app.schemas.document import DocumentCreate, DocumentResponse


class DocumentService:
    """Async service managing technical document metadata and vehicle relationships."""

    @staticmethod
    async def get_documents(
        db: AsyncSession,
        generation_code: Optional[str] = None,
        system: Optional[str] = None,
        document_type: Optional[str] = None,
    ) -> List[DocumentResponse]:
        stmt = (
            select(TechnicalDocument)
            .options(
                joinedload(TechnicalDocument.generation),
                joinedload(TechnicalDocument.engine),
            )
            .order_by(TechnicalDocument.title)
        )

        if generation_code:
            stmt = stmt.join(TechnicalDocument.generation).where(
                Generation.code.ilike(generation_code)
            )
        if system:
            stmt = stmt.where(TechnicalDocument.system == system.lower())
        if document_type:
            stmt = stmt.where(TechnicalDocument.document_type == document_type.lower())

        result = await db.execute(stmt)
        docs = result.scalars().all()

        return [
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                file_path=doc.file_path,
                file_size_bytes=doc.file_size_bytes,
                document_type=doc.document_type,
                system=doc.system,
                language=doc.language,
                generation_id=doc.generation_id,
                engine_id=doc.engine_id,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                generation_code=doc.generation.code if doc.generation else None,
                engine_code=doc.engine.code if doc.engine else None,
            )
            for doc in docs
        ]

    @staticmethod
    async def get_document_by_id(
        db: AsyncSession, document_id: int
    ) -> Optional[DocumentResponse]:
        stmt = (
            select(TechnicalDocument)
            .where(TechnicalDocument.id == document_id)
            .options(
                joinedload(TechnicalDocument.generation),
                joinedload(TechnicalDocument.engine),
            )
        )
        result = await db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            return None

        return DocumentResponse(
            id=doc.id,
            title=doc.title,
            file_path=doc.file_path,
            file_size_bytes=doc.file_size_bytes,
            document_type=doc.document_type,
            system=doc.system,
            language=doc.language,
            generation_id=doc.generation_id,
            engine_id=doc.engine_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            generation_code=doc.generation.code if doc.generation else None,
            engine_code=doc.engine.code if doc.engine else None,
        )

    @staticmethod
    async def create_document(db: AsyncSession, payload: DocumentCreate) -> TechnicalDocument:
        doc = TechnicalDocument(
            title=payload.title,
            file_path=payload.file_path,
            file_size_bytes=payload.file_size_bytes,
            document_type=payload.document_type,
            system=payload.system,
            language=payload.language,
            generation_id=payload.generation_id,
            engine_id=payload.engine_id,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

