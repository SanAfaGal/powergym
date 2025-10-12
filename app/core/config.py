from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Secure FastAPI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str]

    SUPER_ADMIN_USERNAME: str
    SUPER_ADMIN_PASSWORD: str
    SUPER_ADMIN_EMAIL: str
    SUPER_ADMIN_FULL_NAME: str

    SUPABASE_URL: str
    SUPABASE_KEY: str

    DATABASE_URL: str
    ASYNC_DATABASE_URL: str

    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[str] = None
    ADMINER_PORT: Optional[str] = None

    REDIS_URL: Optional[str] = None

    DEBUG: bool = False

    FACE_RECOGNITION_MODEL: str = "hog"
    FACE_RECOGNITION_TOLERANCE: float = 0.6
    MAX_IMAGE_SIZE_MB: int = 5
    ALLOWED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "webp"]

    BIOMETRIC_ENCRYPTION_KEY: str

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    ENABLE_COMPRESSION: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
