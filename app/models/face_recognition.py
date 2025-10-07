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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "client_id": "123e4567-e89b-12d3-a456-426614174000",
                    "image_base64": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/..."
                }
            ]
        }
    }

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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "image_base64": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/..."
                }
            ]
        }
    }

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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "image_base64_1": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/...",
                    "image_base64_2": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/..."
                }
            ]
        }
    }

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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "client_id": "123e4567-e89b-12d3-a456-426614174000",
                    "image_base64": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/..."
                }
            ]
        }
    }

class FaceDeleteResponse(BaseModel):
    success: bool
    message: str
