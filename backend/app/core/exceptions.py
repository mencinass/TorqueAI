from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class AutomotiveAIException(Exception):
    """Base exception for Automotive AI domain errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DatabaseConnectionError(AutomotiveAIException):
    """Raised when the relational database cannot be reached."""

    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class VectorDBConnectionError(AutomotiveAIException):
    """Raised when Qdrant vector database cannot be reached."""

    def __init__(self, message: str = "Vector database connection failed"):
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with FastAPI application."""

    @app.exception_handler(AutomotiveAIException)
    async def handle_automotive_ai_exception(
        request: Request, exc: AutomotiveAIException
    ) -> JSONResponse:
        logger.error(f"Domain error occurred: {exc.message} (path: {request.url.path})")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "message": exc.message},
        )

