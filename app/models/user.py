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

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class User(UserBase):
    disabled: bool = False

    class Config:
        from_attributes = True
        use_enum_values = True

class UserInDB(User):
    hashed_password: str
