from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, roles, clients, face_recognition, monitoring, attendances, plans, payments, subscriptions, products, stock, movements, reports

api_router = APIRouter()

api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clients.router)
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(subscriptions.router)
api_router.include_router(payments.router)
api_router.include_router(face_recognition.router, prefix="/face", tags=["face-recognition"])
api_router.include_router(attendances.router)
api_router.include_router(products.router, prefix="/inventory")
api_router.include_router(stock.router, prefix="/inventory")
api_router.include_router(movements.router, prefix="/inventory")
api_router.include_router(reports.router, prefix="/inventory")
