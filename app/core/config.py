from typing import List, Optional
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de PowerGym Backend"""

    # ==================== APP CONFIG ====================
    PROJECT_NAME: str = "PowerGym API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ==================== SECURITY ====================
    SECRET_KEY: str = Field(..., description="JWT secret key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BIOMETRIC_ENCRYPTION_KEY: str = Field(..., description="Encryption key for biometric data")

    # ==================== CORS & ALLOWED ORIGINS ====================
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:5173"],
        description="Allowed origins for CORS"
    )

    # ==================== SUPER ADMIN ====================
    SUPER_ADMIN_USERNAME: str = Field(..., description="Initial admin username")
    SUPER_ADMIN_PASSWORD: str = Field(..., description="Initial admin password")
    SUPER_ADMIN_EMAIL: str = Field(..., description="Initial admin email")
    SUPER_ADMIN_FULL_NAME: str = Field(..., description="Initial admin full name")

    # ==================== DATABASE ====================
    DATABASE_URL: str = Field(..., description="Sync database URL")
    ASYNC_DATABASE_URL: str = Field(..., description="Async database URL")

    POSTGRES_USER: Optional[str] = Field(None, description="PostgreSQL username")
    POSTGRES_PASSWORD: Optional[str] = Field(None, description="PostgreSQL password")
    POSTGRES_DB: Optional[str] = Field(None, description="PostgreSQL database name")
    POSTGRES_HOST: Optional[str] = Field(None, description="PostgreSQL host")
    POSTGRES_PORT: Optional[int] = Field(None, description="PostgreSQL port")

    # ==================== CACHE ====================
    REDIS_URL: Optional[str] = Field(None, description="Redis connection URL")

    # ==================== FACE RECOGNITION & MEDIAPIPE ====================
    EMBEDDING_DIMENSIONS: int

    # InsightFace
    INSIGHTFACE_MODEL: str = "buffalo_l"  # buffalo_s, buffalo_l, buffalo_sc
    INSIGHTFACE_DET_SIZE: int = 640
    INSIGHTFACE_CTX_ID: int = -1  # -1 para CPU, 0 para GPU

    FACE_RECOGNITION_TOLERANCE: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Tolerance for face recognition (0.0-1.0)"
    )
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum detection confidence for MediaPipe (0.0-1.0)"
    )

    # ==================== IMAGE PROCESSING ====================
    MAX_IMAGE_SIZE_MB: int = Field(
        default=5,
        gt=0,
        description="Maximum image size in MB"
    )
    ALLOWED_IMAGE_FORMATS: List[str] = Field(
        default=["jpg", "jpeg", "png", "webp"],
        description="Allowed image formats"
    )
    IMAGE_COMPRESSION_QUALITY: int = Field(
        default=85,
        ge=1,
        le=100,
        description="Image compression quality (1-100)"
    )
    THUMBNAIL_COMPRESSION_QUALITY: int = Field(
        default=70,
        ge=1,
        le=100,
        description="Thumbnail compression quality (1-100)"
    )
    THUMBNAIL_WIDTH: int = Field(default=150, gt=0, description="Thumbnail width in pixels")
    THUMBNAIL_HEIGHT: int = Field(default=150, gt=0, description="Thumbnail height in pixels")
    EMBEDDING_COMPRESSION_LEVEL: int = Field(
        default=9,
        ge=0,
        le=9,
        description="Embedding compression level (0-9)"
    )
    ENABLE_COMPRESSION: bool = Field(default=True, description="Enable image compression")

    # ==================== RATE LIMITING ====================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        gt=0,
        description="Rate limit requests per minute"
    )

    # ==================== ADMIN UI ====================
    ADMINER_PORT: Optional[int] = Field(None, description="Adminer UI port")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignora variables de entorno no definidas


settings = Settings()