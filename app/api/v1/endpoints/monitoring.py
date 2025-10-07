from fastapi import APIRouter, HTTPException
from app.core.database import get_supabase_client
from app.core.config import settings
from app.core.cache import get_cache_manager
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": time.time()
    }

    try:
        supabase = get_supabase_client()
        response = supabase.table("users").select("id").limit(1).execute()
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
        "face_recognition_model": settings.FACE_RECOGNITION_MODEL,
        "face_recognition_tolerance": settings.FACE_RECOGNITION_TOLERANCE
    }

@router.get("/ready")
async def readiness_check():
    try:
        supabase = get_supabase_client()
        response = supabase.table("users").select("id").limit(1).execute()
        return {"ready": True}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service not ready")
