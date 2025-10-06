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
    pass

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
