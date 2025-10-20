from datetime import datetime
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.schemas.attendance import AttendanceResponse, AttendanceWithClientInfo
from app.schemas.face_recognition import FaceAuthenticationRequest
from app.services.attendance_service import AttendanceService
from app.services.face_recognition.core import FaceRecognitionService
from app.api.dependencies import get_current_user
from app.schemas.user import User
from app.db.session import get_async_db, get_db


router = APIRouter()


@router.post(
    "/check-in",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Check-in with face recognition",
    description="Validate client identity via face recognition and record attendance.",
    responses={
        201: {
            "description": "Check-in successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Check-in successful",
                        "attendance": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "client_id": "987fcdeb-51a2-43f1-9876-543210fedcba",
                            "check_in": "2025-10-07T10:30:00Z",
                        },
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
        401: {"description": "Authentication failed - face not recognized"},
        400: {"description": "Invalid image or no face detected"}
    }
)
async def check_in_with_face(
    request: FaceAuthenticationRequest,
    current_user: User = Depends(get_current_user),
    db_sync: Session = Depends(get_db),
    db_async: AsyncSession = Depends(get_async_db)
):
    """
    Check-in a client using face recognition.

    This endpoint validates the client's identity through facial recognition
    and automatically creates an attendance record upon successful validation.
    """
    auth_result = FaceRecognitionService.authenticate_face(
        db=db_sync,
        image_base64=request.image_base64
    )

    if not auth_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_result.get("error", "Face authentication failed")
        )

    client_id = auth_result.get("client_id")
    confidence = auth_result.get("confidence", 0.0)

    attendance = await AttendanceService.create_attendance(
        db=db_async,
        client_id=UUID(client_id),
        meta_info={
            "confidence": confidence,
            "authenticated_by": str(current_user.username)
        }
    )

    return {
        "success": True,
        "message": "Check-in successful",
        "attendance": {
            "id": str(attendance.id),
            "client_id": str(attendance.client_id),
            "check_in": attendance.check_in.isoformat(),
        },
        "client_info": auth_result.get("client_info"),
        "confidence": confidence
    }


@router.get(
    "/{attendance_id}",
    response_model=AttendanceResponse,
    summary="Get attendance by ID",
    description="Retrieve a specific attendance record by its ID."
)
async def get_attendance(
    attendance_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific attendance record."""
    attendance = await AttendanceService.get_attendance_by_id(db, attendance_id)

    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )

    return attendance


@router.get(
    "/client/{client_id}",
    response_model=List[AttendanceResponse],
    summary="Get client attendances",
    description="Retrieve all attendance records for a specific client."
)
async def get_client_attendances(
    client_id: UUID,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all attendance records for a specific client."""
    attendances = await AttendanceService.get_client_attendances(
        db=db,
        client_id=client_id,
        limit=limit,
        offset=offset
    )

    return attendances


@router.get(
    "",
    response_model=List[AttendanceWithClientInfo],
    summary="Get all attendances",
    description="Retrieve all attendance records with optional date filtering."
)
async def get_all_attendances(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all attendance records with client information."""
    attendances = await AttendanceService.get_all_attendances(
        db=db,
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date
    )

    return attendances


@router.get(
    "/today/all",
    response_model=List[AttendanceWithClientInfo],
    summary="Get today's attendances",
    description="Retrieve all attendance records for today."
)
async def get_today_attendances(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all attendance records for today."""
    attendances = await AttendanceService.get_today_attendances(db)
    return attendances


@router.get(
    "/client/{client_id}/count",
    response_model=dict,
    summary="Count client attendances",
    description="Count attendance records for a client within a date range."
)
async def count_client_attendances(
    client_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Count attendance records for a specific client."""
    count = await AttendanceService.count_client_attendances(
        db=db,
        client_id=client_id,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "client_id": str(client_id),
        "count": count,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None
    }
