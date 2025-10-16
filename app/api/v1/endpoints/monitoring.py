from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_async_db
from app.core.config import settings
from app.core.cache import get_cache_manager
import time

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_async_db)):
    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": time.time()
    }

    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    try:
        cache = get_cache_manager()
        await cache.set("health_check", "ok", ttl=10)
        cached_value = await cache.get("health_check")
        health_status["cache"] = "connected" if cached_value == "ok" else "degraded"
    except Exception as e:
        health_status["cache"] = f"warning: {str(e)}"

    return health_status

@router.get("/metrics")
async def get_metrics():
    return {
        "api_version": settings.VERSION,
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
        "compression_enabled": settings.ENABLE_COMPRESSION,
        "face_recognition_model": "MediaPipe FaceMesh + FaceDetection",
        "face_recognition_tolerance": settings.FACE_RECOGNITION_TOLERANCE,
        "mediapipe_min_detection_confidence": settings.MEDIAPIPE_MIN_DETECTION_CONFIDENCE
    }

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_async_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service not ready")
