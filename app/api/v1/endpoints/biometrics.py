from fastapi import APIRouter, HTTPException, Depends, status, Body
from app.models.biometric import (
    Biometric,
    BiometricCreate,
    BiometricUpdate,
    BiometricType,
    BiometricSearchResult
)
from app.services.biometric_service import BiometricService
from app.api.dependencies import get_current_user
from app.models.user import User
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class BiometricCreateRequest(BaseModel):
    client_id: UUID
    type: BiometricType
    compressed_data: str
    thumbnail: Optional[str] = None
    embedding: Optional[List[float]] = None
    meta_info: dict = {}

class BiometricUpdateRequest(BaseModel):
    compressed_data: Optional[str] = None
    thumbnail: Optional[str] = None
    embedding: Optional[List[float]] = None
    is_active: Optional[bool] = None
    meta_info: Optional[dict] = None

class BiometricSearchRequest(BaseModel):
    embedding: List[float]
    type: Optional[BiometricType] = None
    limit: int = 10
    similarity_threshold: float = 0.8

class BiometricResponse(BaseModel):
    id: UUID
    client_id: UUID
    type: BiometricType
    compressed_data: str
    thumbnail: Optional[str] = None
    embedding: Optional[List[float]] = None
    is_active: bool
    created_at: str
    updated_at: str
    meta_info: dict

    class Config:
        from_attributes = True

@router.post("/", response_model=BiometricResponse, status_code=status.HTTP_201_CREATED)
def create_biometric(
    request: BiometricCreateRequest,
    current_user: User = Depends(get_current_user)
):
    import base64

    try:
        compressed_data_bytes = base64.b64decode(request.compressed_data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 compressed_data"
        )

    thumbnail_bytes = None
    if request.thumbnail:
        try:
            thumbnail_bytes = base64.b64decode(request.thumbnail)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 thumbnail"
            )

    biometric_data = BiometricCreate(
        client_id=request.client_id,
        type=request.type,
        compressed_data=compressed_data_bytes,
        thumbnail=thumbnail_bytes,
        embedding=request.embedding,
        meta_info=request.meta_info
    )

    biometric = BiometricService.create_biometric(biometric_data)

    if not biometric:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create biometric record"
        )

    return BiometricResponse(
        id=biometric.id,
        client_id=biometric.client_id,
        type=biometric.type,
        compressed_data=base64.b64encode(biometric.compressed_data).decode('utf-8'),
        thumbnail=base64.b64encode(biometric.thumbnail).decode('utf-8') if biometric.thumbnail else None,
        embedding=biometric.embedding,
        is_active=biometric.is_active,
        created_at=biometric.created_at,
        updated_at=biometric.updated_at,
        meta_info=biometric.meta_info
    )

@router.get("/{biometric_id}", response_model=BiometricResponse)
def get_biometric(
    biometric_id: UUID,
    current_user: User = Depends(get_current_user)
):
    import base64

    biometric = BiometricService.get_biometric_by_id(biometric_id)

    if not biometric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biometric record not found"
        )

    return BiometricResponse(
        id=biometric.id,
        client_id=biometric.client_id,
        type=biometric.type,
        compressed_data=base64.b64encode(biometric.compressed_data).decode('utf-8'),
        thumbnail=base64.b64encode(biometric.thumbnail).decode('utf-8') if biometric.thumbnail else None,
        embedding=biometric.embedding,
        is_active=biometric.is_active,
        created_at=biometric.created_at,
        updated_at=biometric.updated_at,
        meta_info=biometric.meta_info
    )

@router.get("/client/{client_id}", response_model=List[BiometricResponse])
def get_client_biometrics(
    client_id: UUID,
    type: Optional[BiometricType] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    import base64

    biometrics = BiometricService.get_biometrics_by_client(client_id, type, is_active)

    return [
        BiometricResponse(
            id=bio.id,
            client_id=bio.client_id,
            type=bio.type,
            compressed_data=base64.b64encode(bio.compressed_data).decode('utf-8'),
            thumbnail=base64.b64encode(bio.thumbnail).decode('utf-8') if bio.thumbnail else None,
            embedding=bio.embedding,
            is_active=bio.is_active,
            created_at=bio.created_at,
            updated_at=bio.updated_at,
            meta_info=bio.meta_info
        )
        for bio in biometrics
    ]

@router.put("/{biometric_id}", response_model=BiometricResponse)
def update_biometric(
    biometric_id: UUID,
    request: BiometricUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    import base64

    compressed_data_bytes = None
    if request.compressed_data:
        try:
            compressed_data_bytes = base64.b64decode(request.compressed_data)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 compressed_data"
            )

    thumbnail_bytes = None
    if request.thumbnail:
        try:
            thumbnail_bytes = base64.b64decode(request.thumbnail)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 thumbnail"
            )

    biometric_update = BiometricUpdate(
        compressed_data=compressed_data_bytes,
        thumbnail=thumbnail_bytes,
        embedding=request.embedding,
        is_active=request.is_active,
        meta_info=request.meta_info
    )

    biometric = BiometricService.update_biometric(biometric_id, biometric_update)

    if not biometric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biometric record not found"
        )

    return BiometricResponse(
        id=biometric.id,
        client_id=biometric.client_id,
        type=biometric.type,
        compressed_data=base64.b64encode(biometric.compressed_data).decode('utf-8'),
        thumbnail=base64.b64encode(biometric.thumbnail).decode('utf-8') if biometric.thumbnail else None,
        embedding=biometric.embedding,
        is_active=biometric.is_active,
        created_at=biometric.created_at,
        updated_at=biometric.updated_at,
        meta_info=biometric.meta_info
    )

@router.delete("/{biometric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_biometric(
    biometric_id: UUID,
    current_user: User = Depends(get_current_user)
):
    success = BiometricService.delete_biometric(biometric_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biometric record not found"
        )

    return None

@router.post("/{biometric_id}/deactivate", response_model=BiometricResponse)
def deactivate_biometric(
    biometric_id: UUID,
    current_user: User = Depends(get_current_user)
):
    import base64

    biometric = BiometricService.deactivate_biometric(biometric_id)

    if not biometric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biometric record not found"
        )

    return BiometricResponse(
        id=biometric.id,
        client_id=biometric.client_id,
        type=biometric.type,
        compressed_data=base64.b64encode(biometric.compressed_data).decode('utf-8'),
        thumbnail=base64.b64encode(biometric.thumbnail).decode('utf-8') if biometric.thumbnail else None,
        embedding=biometric.embedding,
        is_active=biometric.is_active,
        created_at=biometric.created_at,
        updated_at=biometric.updated_at,
        meta_info=biometric.meta_info
    )

@router.post("/search", response_model=List[BiometricSearchResult])
def search_biometrics(
    request: BiometricSearchRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    if len(request.embedding) != 512:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Embedding must have exactly 512 dimensions"
        )

    results = BiometricService.search_by_embedding(
        embedding=request.embedding,
        biometric_type=request.type,
        limit=request.limit,
        similarity_threshold=request.similarity_threshold
    )

    return results

@router.get("/", response_model=List[BiometricResponse])
def list_biometrics(
    type: Optional[BiometricType] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    import base64

    biometrics = BiometricService.list_biometrics(type, is_active, limit, offset)

    return [
        BiometricResponse(
            id=bio.id,
            client_id=bio.client_id,
            type=bio.type,
            compressed_data=base64.b64encode(bio.compressed_data).decode('utf-8'),
            thumbnail=base64.b64encode(bio.thumbnail).decode('utf-8') if bio.thumbnail else None,
            embedding=bio.embedding,
            is_active=bio.is_active,
            created_at=bio.created_at,
            updated_at=bio.updated_at,
            meta_info=bio.meta_info
        )
        for bio in biometrics
    ]
