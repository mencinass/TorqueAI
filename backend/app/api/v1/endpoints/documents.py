from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services.document_service import DocumentService
from app.services.thumbnail_service import PageThumbnailService

router = APIRouter()


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="List technical documents with vehicle context filters",
    description="Retrieve service manuals and diagrams filtered by chassis generation code, automotive system, or document type.",
)
async def list_documents(
    generation: Optional[str] = Query(
        None, description="Filter by generation code (e.g. R56, R53, 312)"
    ),
    system: Optional[str] = Query(
        None, description="Filter by automotive system (e.g. steering, engine, brakes)"
    ),
    document_type: Optional[str] = Query(
        None, description="Filter by document type (e.g. workshop_manual, repair_manual)"
    ),
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService.get_documents(
        db, generation_code=generation, system=system, document_type=document_type
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get technical document metadata by ID",
)
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technical document with ID {document_id} not found",
        )
    return doc


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new technical service manual or diagram",
)
async def create_document(payload: DocumentCreate, db: AsyncSession = Depends(get_db)):
    created = await DocumentService.create_document(db, payload)
    return await DocumentService.get_document_by_id(db, created.id)


@router.get(
    "/{document_id}/page/{page_number}/thumbnail",
    response_class=FileResponse,
    summary="Render a page thumbnail for a document",
    description="Renders a single PDF page as a PNG (cached), for source validation in the chat UI.",
)
async def document_page_thumbnail(
    document_id: int,
    page_number: int,
    db: AsyncSession = Depends(get_db),
):
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technical document with ID {document_id} not found",
        )

    service = PageThumbnailService()
    try:
        path = await service.render(document_id, page_number, doc.file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on disk",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Thumbnail render failed: {exc}"
        )

    return FileResponse(
        path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )

