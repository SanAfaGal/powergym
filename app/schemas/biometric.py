from pydantic import BaseModel, field_validator
from enum import Enum
from uuid import UUID
from typing import Optional, List

class BiometricType(str, Enum):
    FACE = "face"
    FINGERPRINT = "fingerprint"

class BiometricBase(BaseModel):
    client_id: UUID
    type: BiometricType
    thumbnail: Optional[str] = None
    embedding_vector: Optional[List[float]] = None
    is_active: bool = True
    meta_info: dict = {}

class BiometricCreate(BaseModel):
    client_id: UUID
    type: BiometricType
    thumbnail: Optional[str] = None
    embedding_vector: Optional[List[float]] = None
    meta_info: dict = {}

class BiometricUpdate(BaseModel):
    thumbnail: Optional[str] = None
    embedding_vector: Optional[List[float]] = None
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
