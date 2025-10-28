"""
Inventory Movements Endpoints Module

FastAPI routes for inventory movement tracking and management.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.schemas.inventory import (
    InventoryMovementResponse,
)
from app.schemas.user import User
from app.services.inventory_service import MovementService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/movements", tags=["Movements"])


# ============================================================
# READ OPERATIONS
# ============================================================

@router.get(
    "/{movement_id}",
    response_model=InventoryMovementResponse,
    summary="Get movement by ID",
    responses={
        200: {
            "description": "Movement found",
            "model": InventoryMovementResponse,
            "content": {
                "application/json": {
                    "example": {
                        "id": "mov-uuid-1",
                        "product_id": "prod-uuid-1",
                        "movement_type": "EXIT",
                        "quantity": -15,
                        "movement_date": "2025-01-15T12:30:00Z",
                        "responsible": "juan",
                        "notes": "Sale transaction #1234"
                    }
                }
            }
        },
        404: {
            "description": "Movement not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Movement mov-uuid-xyz not found"}
                }
            }
        },
    }
)
def get_movement(
        movement_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> InventoryMovementResponse:
    """
    Retrieve movement by ID.

    **Permissions:** Any authenticated user

    **Path Parameters:**
    - movement_id: Movement UUID (required)

    **Response Schema (InventoryMovementResponse):**
    - id: Movement unique identifier
    - product_id: Associated product UUID
    - movement_type: Type of movement (ENTRY, EXIT, ADJUSTMENT)
    - quantity: Amount moved (positive for ENTRY, negative for EXIT, any for ADJUSTMENT)
    - movement_date: Timestamp when movement was recorded (UTC, auto-converted to local timezone)
    - responsible: Username of person responsible for movement (optional)
    - notes: Additional notes or comments (optional)

    **Error Cases:**
    - 404: Movement not found
    - 401: Unauthorized (not authenticated)
    """
    logger.debug(f"User {current_user.username} fetching movement: {movement_id}")
    service = MovementService(db)
    movement = service.get_movement(movement_id)

    if not movement:
        logger.warning(f"Movement not found: {movement_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movement {movement_id} not found"
        )

    return movement


@router.get(
    "",
    response_model=dict,
    summary="List all movements with pagination",
    responses={
        200: {
            "description": "List of movements",
            "content": {
                "application/json": {
                    "example": {
                        "skip": 0,
                        "limit": 100,
                        "total": 245,
                        "items": [
                            {
                                "id": "mov-uuid-1",
                                "product_id": "prod-uuid-1",
                                "movement_type": "EXIT",
                                "quantity": -15,
                                "movement_date": "2025-01-15T12:30:00Z",
                                "responsible": "juan",
                                "notes": "Sale transaction"
                            },
                            {
                                "id": "mov-uuid-2",
                                "product_id": "prod-uuid-1",
                                "movement_type": "ENTRY",
                                "quantity": 100,
                                "movement_date": "2025-01-15T10:00:00Z",
                                "responsible": None,
                                "notes": "Stock replenishment"
                            },
                            {
                                "id": "mov-uuid-3",
                                "product_id": "prod-uuid-2",
                                "movement_type": "ADJUSTMENT",
                                "quantity": -5,
                                "movement_date": "2025-01-14T16:45:00Z",
                                "responsible": "admin",
                                "notes": "Inventory count adjustment"
                            }
                        ]
                    }
                }
            }
        }
    }
)
def list_movements(
        skip: int = Query(0, ge=0, description="Number of movements to skip (pagination offset)"),
        limit: int = Query(100, ge=1, le=100, description="Maximum movements per page (max: 100)"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    List all movements with pagination.

    **Permissions:** Any authenticated user

    Returns paginated list of all inventory movements sorted by date (newest first).

    **Query Parameters:**
    - skip: Number of movements to skip for pagination (default: 0)
    - limit: Maximum movements to return per page (default: 100, max: 100)

    **Response Schema:**
    - skip: Pagination offset used in query
    - limit: Pagination limit used in query
    - total: Total count of all movements available
    - items: Array of InventoryMovementResponse objects

    **InventoryMovementResponse fields:**
    - id: Movement unique identifier
    - product_id: Associated product UUID
    - movement_type: Type of movement (ENTRY, EXIT, ADJUSTMENT)
    - quantity: Amount moved
    - movement_date: Timestamp in UTC (auto-converted to local timezone in response)
    - responsible: Person responsible (optional)
    - notes: Additional notes (optional)

    **Error Cases:**
    - 401: Unauthorized (not authenticated)
    """
    logger.debug(
        f"User {current_user.username} listing movements: skip={skip}, limit={limit}"
    )
    service = MovementService(db)
    movements, total = service.get_all_movements(skip, limit)

    return {
        "skip": skip,
        "limit": limit,
        "total": total,
        "items": movements
    }