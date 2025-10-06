from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Secure FastAPI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    SUPER_ADMIN_USERNAME: str = "admin"
    SUPER_ADMIN_PASSWORD: str = "changeme123"
    SUPER_ADMIN_EMAIL: str = "admin@company.com"
    SUPER_ADMIN_FULL_NAME: str = "Super Administrator"

    SUPABASE_URL: str
    SUPABASE_KEY: str

    FACE_RECOGNITION_MODEL: str = "hog"
    FACE_RECOGNITION_TOLERANCE: float = 0.6
    MAX_IMAGE_SIZE_MB: int = 5
    ALLOWED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "webp"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
