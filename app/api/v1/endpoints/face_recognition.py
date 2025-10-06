from fastapi import APIRouter, HTTPException, Depends, status
from app.models.face_recognition import (
    FaceRegistrationRequest,
    FaceRegistrationResponse,
    FaceAuthenticationRequest,
    FaceAuthenticationResponse,
    FaceComparisonRequest,
    FaceComparisonResponse,
    FaceUpdateRequest,
    FaceDeleteResponse
)
from app.services.face_recognition_service import FaceRecognitionService
from app.services.client_service import ClientService
from app.api.dependencies import get_current_user
from app.models.user import User
from uuid import UUID

router = APIRouter()

@router.post("/register", response_model=FaceRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_client_face(
    request: FaceRegistrationRequest,
    current_user: User = Depends(get_current_user)
):
    client = ClientService.get_client_by_id(request.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="client not found"
        )

    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client is not active"
        )

    result = FaceRecognitionService.register_face(
        client_id=request.client_id,
        image_base64=request.image_base64
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to register face")
        )

    return FaceRegistrationResponse(
        success=True,
        message="Face registered successfully",
        biometric_id=result.get("biometric_id"),
        client_id=result.get("client_id")
    )

@router.post("/authenticate", response_model=FaceAuthenticationResponse)
async def authenticate_client_face(
    request: FaceAuthenticationRequest,
    current_user: User = Depends(get_current_user)
):
    result = FaceRecognitionService.authenticate_face(
        image_base64=request.image_base64
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Authentication failed")
        )

    return FaceAuthenticationResponse(
        success=True,
        message="Face authenticated successfully",
        client_id=result.get("client_id"),
        client_info=result.get("client_info"),
        confidence=result.get("confidence")
    )

@router.post("/compare", response_model=FaceComparisonResponse)
async def compare_faces(
    request: FaceComparisonRequest,
    current_user: User = Depends(get_current_user)
):
    result = FaceRecognitionService.compare_two_faces(
        image_base64_1=request.image_base64_1,
        image_base64_2=request.image_base64_2
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to compare faces")
        )

    return FaceComparisonResponse(
        success=True,
        message="Faces compared successfully",
        match=result.get("match"),
        distance=result.get("distance"),
        confidence=result.get("confidence")
    )

@router.put("/update", response_model=FaceRegistrationResponse)
async def update_client_face(
    request: FaceUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    client = ClientService.get_client_by_id(request.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="client not found"
        )

    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client is not active"
        )

    result = FaceRecognitionService.update_face(
        client_id=request.client_id,
        image_base64=request.image_base64
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to update face")
        )

    return FaceRegistrationResponse(
        success=True,
        message="Face updated successfully",
        biometric_id=result.get("biometric_id"),
        client_id=result.get("client_id")
    )

@router.delete("/{client_id}", response_model=FaceDeleteResponse)
async def delete_client_face(
    client_id: UUID,
    current_user: User = Depends(get_current_user)
):
    client = ClientService.get_client_by_id(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="client not found"
        )

    result = FaceRecognitionService.delete_face(client_id=client_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to delete face biometric")
        )

    return FaceDeleteResponse(
        success=True,
        message="Face biometric deleted successfully"
    )
