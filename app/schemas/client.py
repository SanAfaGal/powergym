from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import date
from uuid import UUID

class DocumentType(str, Enum):
    CC = "CC"
    TI = "TI"
    CE = "CE"
    PP = "PP"

class GenderType(str, Enum):
    M = "male"
    F = "female"
    O = "other"

class ClientBase(BaseModel):
    dni_type: DocumentType
    dni_number: str
    first_name: str
    middle_name: str | None = None
    last_name: str
    second_last_name: str | None = None
    phone: str
    alternative_phone: str | None = None
    birth_date: date
    gender: GenderType
    address: str | None = None

    @field_validator('dni_number')
    @classmethod
    def validate_dni_number(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('DNI number cannot be empty')
        return v.strip()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Phone number cannot be empty')
        return v.strip()

class ClientCreate(ClientBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "dni_type": "CC",
                    "dni_number": "1234567890",
                    "first_name": "Juan",
                    "middle_name": "Carlos",
                    "last_name": "Pérez",
                    "second_last_name": "González",
                    "phone": "+573001234567",
                    "alternative_phone": "+573109876543",
                    "birth_date": "1990-05-15",
                    "gender": "male",
                    "address": "Calle 123 #45-67, Bogotá"
                }
            ]
        }
    }

class ClientUpdate(BaseModel):
    dni_type: DocumentType | None = None
    dni_number: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    second_last_name: str | None = None
    phone: str | None = None
    alternative_phone: str | None = None
    birth_date: date | None = None
    gender: GenderType | None = None
    address: str | None = None
    is_active: bool | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "phone": "+573001111111",
                    "address": "Carrera 7 #32-16, Medellín",
                    "is_active": True
                }
            ]
        }
    }

class Client(ClientBase):
    id: UUID
    is_active: bool
    created_at: str
    updated_at: str
    meta_info: dict = {}

    class Config:
        from_attributes = True
        use_enum_values = True

class ClientInDB(Client):
    pass


from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional
from datetime import date, datetime


class ClientBasicInfo(BaseModel):
    """Basic client information for dashboard."""
    id: UUID
    first_name: str
    last_name: str
    dni_type: str
    dni_number: str
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BiometricInfo(BaseModel):
    """Biometric information for dashboard."""
    type: Optional[str] = None
    thumbnail: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionInfo(BaseModel):
    """Subscription information for dashboard."""
    status: Optional[str] = None
    plan: Optional[str] = None
    end_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class ClientStats(BaseModel):
    """Client statistics for dashboard."""
    subscriptions: Optional[int] = None
    attendances: Optional[int] = None
    last_attendance: Optional[datetime] = None
    since: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClientDashboard(BaseModel):
    """Complete client dashboard information."""
    client: Optional[ClientBasicInfo] = None
    biometric: Optional[BiometricInfo] = None
    subscription: Optional[SubscriptionInfo] = None
    stats: Optional[ClientStats] = None

    model_config = ConfigDict(from_attributes=True)