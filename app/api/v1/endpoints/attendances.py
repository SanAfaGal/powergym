# ============================================================================
# attendance/routes.py - CHECK-IN ENDPOINT (SYNC VERSION)
# ============================================================================

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.dependencies import get_current_user
import logging
from app.schemas.user import User
from app.schemas.face_recognition import FaceAuthenticationRequest
from app.schemas.attendance import (
    AttendanceResponse,
    AttendanceWithClientInfo,
    CheckInResponse
)
from app.services.attendance_service import AttendanceService
from app.services.face_recognition.core import FaceRecognitionService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["attendances"])


# ============================================================================
# IMPORTANTE: Las rutas específicas DEBEN ir ANTES de las rutas con parámetros
# ============================================================================

@router.post(
    "/check-in",
    response_model=CheckInResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Check-in with facial recognition",
    description="Validates client identity and records gym entry.",
    responses={
        201: {
            "description": "Entry recorded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Welcome to the gym",
                        "can_enter": True,
                        "attendance": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "client_id": "550e8400-e29b-41d4-a716-446655440001",
                            "check_in": "2025-10-22T10:30:00Z",
                            "meta_info": {}
                        },
                        "client_info": {
                            "first_name": "John",
                            "last_name": "Doe",
                            "dni_number": "1234567890"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid image or no face detected",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No face detected in the image",
                        "error": "no_face_detected"
                    }
                }
            }
        },
        401: {
            "description": "Face not recognized or insufficient confidence",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Face not recognized in the system",
                        "error": "face_not_recognized"
                    }
                }
            }
        },
        403: {
            "description": "Access denied: inactive client, expired subscription, etc",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Access denied",
                        "can_enter": False,
                        "reason": "subscription_expired",
                        "detail": "Your subscription expired on 2025-10-20. Renew it to continue."
                    }
                }
            }
        },
        409: {
            "description": "Already checked in today",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "You have already checked in today",
                        "can_enter": False,
                        "reason": "already_checked_in",
                        "detail": "Last check-in: 2025-10-24T08:30:00Z"
                    }
                }
            }
        }
    }
)
def check_in_with_face(
        request: FaceAuthenticationRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Record client entry via facial recognition.

    **Flow:**
    1. Validates image and detects face
    2. Recognizes client via facial recognition
    3. Verifies client status and subscription
    4. Checks if already checked in today
    5. Records attendance if everything is valid

    **Response codes:**
    - `201`: Entry recorded successfully (can enter)
    - `400`: Invalid image or no face detected (technical issue)
    - `401`: Face not recognized (client not identified)
    - `403`: Access denied (client/subscription invalid)
    - `409`: Already checked in today

    **Frontend should:**
    - Capture photo from webcam
    - Send as base64 in `image_base64`
    - Show "processing" animation during request
    - Handle each HTTP code with specific messages
    """

    # 1. Validate image and recognize face (SYNC)
    face_result = FaceRecognitionService.authenticate_face(
        db=db,
        image_base64=request.image_base64
    )

    if not face_result.get("success"):
        error_reason = face_result.get("error")
        # 400 for image issues, 401 for unrecognized face
        response_status = (
            status.HTTP_400_BAD_REQUEST
            if error_reason in ["no_face_detected", "invalid_image", "blurry_image"]
            else status.HTTP_401_UNAUTHORIZED
        )
        raise HTTPException(
            status_code=response_status,
            detail=face_result.get("detail", "Facial recognition failed"),
            headers={"X-Error-Reason": error_reason}
        )

    client_id = UUID(face_result.get("client_id"))

    # 2. Validate client access (SYNC) - Incluye verificación de check-in duplicado
    can_access, reason, details = AttendanceService.validate_client_access(
        db, client_id
    )

    # If cannot access, return appropriate error with details
    if not can_access:
        # 409 para check-in duplicado, 403 para otros casos
        response_status = (
            status.HTTP_409_CONFLICT
            if reason == "already_checked_in"
            else status.HTTP_403_FORBIDDEN
        )

        raise HTTPException(
            status_code=response_status,
            detail=_get_denial_message(reason, details),
            headers={"X-Denial-Reason": reason}
        )

    # 3. Record attendance (SYNC)
    attendance = AttendanceService.create_attendance(
        db=db,
        client_id=client_id,
        meta_info={
            "ip": getattr(current_user, "ip", None),
            "authenticated_by": current_user.username
        }
    )

    return CheckInResponse(
        success=True,
        message="Welcome to the gym",
        can_enter=True,
        attendance=attendance,
        client_info=details
    )


@router.get(
    "/attendances",
    response_model=list[AttendanceWithClientInfo],
    status_code=status.HTTP_200_OK,
    summary="Get all attendances",
    description="Gets all system attendances with client info (requires admin)."
)
def get_all_attendances(
        limit: int = Query(100, ge=1, le=1000, description="Records per page"),
        offset: int = Query(0, ge=0, description="Skip records"),
        start_date: Optional[datetime] = Query(
            None,
            description="Start date (ISO 8601): 2025-10-01T00:00:00Z"
        ),
        end_date: Optional[datetime] = Query(
            None,
            description="End date (ISO 8601): 2025-10-31T23:59:59Z"
        ),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all system attendances with filters.

    **Parameters:**
    - `limit`: Records per page (max 1000)
    - `offset`: For pagination
    - `start_date`: Filter from date (optional)
    - `end_date`: Filter until date (optional)

    **Codes:**
    - `200`: Attendances retrieved (may be empty list)

    **Frontend can:**
    - Use for general dashboard
    - Filter by date range
    - Export to CSV/PDF
    """
    attendances = AttendanceService.get_all_attendances(
        db=db,
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date
    )
    return attendances


@router.get(
    "/clients/{client_id}",
    response_model=list[AttendanceResponse],
    status_code=status.HTTP_200_OK,
    summary="Client attendance history",
    description="Gets all recorded entries for a client with pagination."
)
def get_client_attendances(
        client_id: UUID,
        limit: int = Query(50, ge=1, le=500, description="Records per page"),
        offset: int = Query(0, ge=0, description="Skip records"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all entries for a client.

    **Parameters:**
    - `client_id`: Client UUID
    - `limit`: Number of records (max 500)
    - `offset`: For pagination

    **Codes:**
    - `200`: History retrieved (may be empty list)

    **Frontend can:**
    - Implement infinite scroll with offset
    - Show "No records" if returns empty list
    """
    attendances = AttendanceService.get_client_attendances(
        db=db,
        client_id=client_id,
        limit=limit,
        offset=offset
    )
    return attendances


@router.get(
    "/{attendance_id}",
    response_model=AttendanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get attendance by ID",
    description="Retrieves details of a specific attendance record."
)
def get_attendance(
        attendance_id: UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get full details of an attendance record.

    **Codes:**
    - `200`: Attendance found
    - `404`: Attendance does not exist
    """
    attendance = AttendanceService.get_by_id(db, attendance_id)

    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )

    return attendance


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_denial_message(reason: str, details: Optional[dict] = None) -> str:
    """
    Get readable message for access denial.

    Maps reason codes to user-facing messages.

    Args:
        reason: Código de la razón de denegación
        details: Información adicional sobre la denegación
    """
    messages = {
        "no_subscription": (
            "You do not have an active subscription. Buy a plan to access."
        ),
        "subscription_expired": (
            "Your subscription has expired. Renew it to continue."
        ),
        "client_inactive": (
            "Your account is disabled. Contact administration."
        ),
        "client_not_found": (
            "Your profile was not found in the system."
        ),
        "already_checked_in": (
            f"You have already checked in today at "
            f"{details.get('check_in_time', 'earlier today') if details else 'earlier today'}. "
            "See you tomorrow!"
        )
    }

    base_message = messages.get(
        reason,
        "Access denied. Please contact administration."
    )

    # Agregar detalles adicionales si están disponibles
    if details and reason == "subscription_expired":
        expired_date = details.get("expired_date", "")
        if expired_date:
            return f"{base_message} (Expired: {expired_date})"

    return base_message