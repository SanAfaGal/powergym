from pydantic import BaseModel, field_validator
from enum import Enum
from uuid import UUID
from typing import Optional

class BiometricType(str, Enum):
    FACE = "face"
    FINGERPRINT = "fingerprint"

class BiometricBase(BaseModel):
    client_id: UUID
    type: BiometricType
    compressed_data: str
    thumbnail: Optional[str] = None
    embedding: Optional[str] = None
    is_active: bool = True
    meta_info: dict = {}

class BiometricCreate(BaseModel):
    client_id: UUID
    type: BiometricType
    compressed_data: str
    thumbnail: Optional[str] = None
    embedding: Optional[str] = None
    meta_info: dict = {}

class BiometricUpdate(BaseModel):
    compressed_data: Optional[str] = None
    thumbnail: Optional[str] = None
    embedding: Optional[str] = None
    is_active: Optional[bool] = None
    meta_info: Optional[dict] = None

class Biometric(BiometricBase):
    id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
        use_enum_values = True

class BiometricInDB(Biometric):
    pass

class BiometricSearchResult(BaseModel):
    biometric: Biometric
    similarity: float
    client_info: Optional[dict] = None

    class Config:
        from_attributes = True
