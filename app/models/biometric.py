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
    compressed_data: bytes
    thumbnail: Optional[bytes] = None
    embedding: Optional[list[float]] = None
    is_active: bool = True
    meta_info: dict = {}

    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: Optional[list[float]]) -> Optional[list[float]]:
        if v is not None and len(v) != 512:
            raise ValueError('Embedding must have exactly 512 dimensions')
        return v

class BiometricCreate(BaseModel):
    client_id: UUID
    type: BiometricType
    compressed_data: bytes
    thumbnail: Optional[bytes] = None
    embedding: Optional[list[float]] = None
    meta_info: dict = {}

    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: Optional[list[float]]) -> Optional[list[float]]:
        if v is not None and len(v) != 512:
            raise ValueError('Embedding must have exactly 512 dimensions')
        return v

class BiometricUpdate(BaseModel):
    compressed_data: Optional[bytes] = None
    thumbnail: Optional[bytes] = None
    embedding: Optional[list[float]] = None
    is_active: Optional[bool] = None
    meta_info: Optional[dict] = None

    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: Optional[list[float]]) -> Optional[list[float]]:
        if v is not None and len(v) != 512:
            raise ValueError('Embedding must have exactly 512 dimensions')
        return v

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
