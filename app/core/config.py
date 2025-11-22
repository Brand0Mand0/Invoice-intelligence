from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # NEAR AI Configuration
    NEAR_AI_API_KEY: str
    NEAR_AI_BASE_URL: str = "https://api.near.ai"

    # Database Configuration
    DATABASE_URL: str

    # Server Configuration
    STREAMLIT_PORT: int = 8501
    FASTAPI_PORT: int = 8000

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # CORS Configuration
    # Comma-separated list of allowed origins
    # Development: http://localhost:8501,http://127.0.0.1:8501
    # Production: https://yourdomain.com,https://www.yourdomain.com
    ALLOWED_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"

    # Processing Configuration
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "/tmp/invoice_uploads"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
