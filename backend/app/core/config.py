from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings validated with Pydantic."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Project metadata
    PROJECT_NAME: str = "TorqueAI"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "automotive-ai-insecure-dev-secret-key-change-me"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL configuration
    POSTGRES_USER: str = "automotive_user"
    POSTGRES_PASSWORD: str = "automotive_pass"
    POSTGRES_DB: str = "automotive_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    # Qdrant Vector Database
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "automotive_manuals"

    # Embedding configuration
    EMBEDDING_PROVIDER: str = "ollama"  # ollama | openai | mock
    EMBEDDING_MODEL: str = "bge-m3"
    EMBEDDING_DIM: int = 1024
    EMBEDDING_OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Local chat generation
    CHAT_PROVIDER: str = "ollama"  # ollama | nvidia | extractive
    CHAT_MODEL: str = "qwen2.5:7b"
    CHAT_TIMEOUT: float = 120.0
    CHAT_TEMPERATURE: float = 0.2
    CHAT_MAX_TOKENS: int = 800
    CHAT_MIN_SCORE: float = 0.2
    AUTO_INGEST_ENABLED: bool = False
    AUTO_INGEST_FORCE: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # NVIDIA NIM (OpenAI-compatible) chat provider
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_CHAT_MODEL: str = "deepseek-ai/deepseek-v4-pro-0813"
    NVIDIA_RATE_LIMIT_RPM: int = 40

    @model_validator(mode="after")
    def assemble_database_url(self) -> "Settings":
        """Build async PostgreSQL URL if not explicitly provided."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self


settings = Settings()

