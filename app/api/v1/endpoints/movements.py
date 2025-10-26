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
)
def get_movement(
        movement_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> InventoryMovementResponse:
    """
    Retrieve movement by ID.

    Args:
        movement_id: Movement UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        InventoryMovementResponse

    Raises:
        HTTPException 404: If movement not found
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
)
def list_movements(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    List all movements with pagination.

    Args:
        skip: Number of movements to skip
        limit: Maximum movements per page (max: 100)
        db: Database session
        current_user: Authenticated user

    Returns:
        Dictionary with movements list and total count
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
