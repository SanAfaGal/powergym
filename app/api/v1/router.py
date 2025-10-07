from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, roles, clients, face_recognition, monitoring, attendances

api_router = APIRouter()

api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(face_recognition.router, prefix="/face", tags=["face-recognition"])
api_router.include_router(attendances.router, prefix="/attendances", tags=["attendances"])
