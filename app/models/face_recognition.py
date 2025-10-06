from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional

class FaceRegistrationRequest(BaseModel):
    client_id: UUID
    image_base64: str

    @field_validator('image_base64')
    @classmethod
    def validate_image_base64(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Image data cannot be empty')
        return v.strip()

class FaceRegistrationResponse(BaseModel):
    success: bool
    message: str
    biometric_id: Optional[UUID] = None
    client_id: Optional[UUID] = None

class FaceAuthenticationRequest(BaseModel):
    image_base64: str

    @field_validator('image_base64')
    @classmethod
    def validate_image_base64(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Image data cannot be empty')
        return v.strip()

class FaceAuthenticationResponse(BaseModel):
    success: bool
    message: str
    client_id: Optional[UUID] = None
    client_info: Optional[dict] = None
    confidence: Optional[float] = None

class FaceComparisonRequest(BaseModel):
    image_base64_1: str
    image_base64_2: str

    @field_validator('image_base64_1', 'image_base64_2')
    @classmethod
    def validate_image_base64(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Image data cannot be empty')
        return v.strip()

class FaceComparisonResponse(BaseModel):
    success: bool
    message: str
    match: bool
    distance: Optional[float] = None
    confidence: Optional[float] = None

class FaceUpdateRequest(BaseModel):
    client_id: UUID
    image_base64: str

    @field_validator('image_base64')
    @classmethod
    def validate_image_base64(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Image data cannot be empty')
        return v.strip()

class FaceDeleteResponse(BaseModel):
    success: bool
    message: str
