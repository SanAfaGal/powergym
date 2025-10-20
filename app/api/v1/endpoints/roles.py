from fastapi import APIRouter
from app.schemas.user import UserRole

router = APIRouter()

@router.get("")
async def list_roles():
    return {
        "roles": [role.value for role in UserRole],
        "descriptions": {
            "admin": "Administrator with full access to all features",
            "employee": "Regular user with limited access"
        }
    }
