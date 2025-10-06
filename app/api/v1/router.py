from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, roles, clients, biometrics, face_recognition

api_router = APIRouter()

api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
# api_router.include_router(biometrics.router, prefix="/biometrics", tags=["biometrics"])
api_router.include_router(face_recognition.router, prefix="/face", tags=["face-recognition"])
