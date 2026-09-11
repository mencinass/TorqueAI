from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, documents, health, ingestion, vehicles

api_router = APIRouter()

# Include feature endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["Vehicle Catalog"])
api_router.include_router(documents.router, prefix="/documents", tags=["Technical Documents"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Document Ingestion"])
api_router.include_router(chat.router, prefix="/chat", tags=["Agent Chat"])