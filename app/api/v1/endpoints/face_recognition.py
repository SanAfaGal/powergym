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

@router.post(
    "/register",
    response_model=FaceRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register face biometric",
    description="Register a client's face biometric data for facial recognition.",
    responses={
        201: {
            "description": "Face registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Face registered successfully",
                        "biometric_id": "123e4567-e89b-12d3-a456-426614174000",
                        "client_id": "987fcdeb-51a2-43f1-9876-543210fedcba"
                    }
                }
            }
        },
        400: {"description": "Invalid image or no face detected"},
        404: {"description": "Client not found"},
        401: {"description": "Not authenticated"}
    }
)
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

@router.post(
    "/authenticate",
    response_model=FaceAuthenticationResponse,
    summary="Authenticate with face",
    description="Authenticate a client by comparing their face with registered biometrics.",
    responses={
        200: {
            "description": "Face authenticated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Face authenticated successfully",
                        "client_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
                        "client_info": {
                            "first_name": "Juan",
                            "last_name": "Pérez",
                            "dni_number": "12345678"
                        },
                        "confidence": 0.95
                    }
                }
            }
        },
        401: {"description": "Authentication failed - no matching face found"},
        400: {"description": "Invalid image or no face detected"}
    }
)
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

@router.post(
    "/compare",
    response_model=FaceComparisonResponse,
    summary="Compare two faces",
    description="Compare two face images to determine if they belong to the same person.",
    responses={
        200: {
            "description": "Faces compared successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Faces compared successfully",
                        "match": True,
                        "distance": 0.35,
                        "confidence": 0.92
                    }
                }
            }
        },
        400: {"description": "Invalid images or no faces detected"},
        401: {"description": "Not authenticated"}
    }
)
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

@router.put(
    "/update",
    response_model=FaceRegistrationResponse,
    summary="Update face biometric",
    description="Update a client's face biometric data with a new image.",
    responses={
        200: {
            "description": "Face updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Face updated successfully",
                        "biometric_id": "123e4567-e89b-12d3-a456-426614174000",
                        "client_id": "987fcdeb-51a2-43f1-9876-543210fedcba"
                    }
                }
            }
        },
        400: {"description": "Invalid image or no face detected"},
        404: {"description": "Client not found"},
        401: {"description": "Not authenticated"}
    }
)
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

@router.delete(
    "/{client_id}",
    response_model=FaceDeleteResponse,
    summary="Delete face biometric",
    description="Delete all face biometric data for a specific client.",
    responses={
        200: {
            "description": "Face biometric deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Face biometric deleted successfully"
                    }
                }
            }
        },
        404: {"description": "Client not found"},
        400: {"description": "Failed to delete face biometric"},
        401: {"description": "Not authenticated"}
    }
)
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
