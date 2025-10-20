from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"

class UserBase(BaseModel):
    username: str
    email: EmailStr | None = None
    full_name: str | None = None
    role: UserRole

class UserCreate(UserBase):
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "role": "employee",
                    "password": "SecureP@ssw0rd123"
                }
            ]
        }
    }

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "newemail@example.com",
                    "full_name": "John Updated Doe"
                }
            ]
        }
    }

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_password": "OldP@ssw0rd123",
                    "new_password": "NewSecureP@ssw0rd456"
                }
            ]
        }
    }

class User(UserBase):
    disabled: bool = False

    class Config:
        from_attributes = True
        use_enum_values = True

class UserInDB(User):
    hashed_password: str
