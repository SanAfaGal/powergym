import warnings
warnings.filterwarnings('ignore', message='pkg_resources is deprecated')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.services.user_service import UserService
from app.db.session import SessionLocal
from app.middleware.compression import CompressionMiddleware
from app.middleware.logging import StructuredLoggingMiddleware
from app.middleware.error_handler import setup_exception_handlers
from app.middleware.rate_limit import setup_rate_limiting

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        UserService.initialize_super_admin(db)
    finally:
        db.close()

app.add_middleware(StructuredLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENABLE_COMPRESSION:
    app.add_middleware(CompressionMiddleware, minimum_size=1000)

setup_exception_handlers(app)
setup_rate_limiting(app)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "API is running", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
