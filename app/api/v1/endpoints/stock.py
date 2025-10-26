"""
Stock Management Endpoints Module

FastAPI routes for inventory stock operations (add/remove).
"""

import logging
from typing import Annotated, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.schemas.user import User
from app.services.inventory_service import ProductService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stock", tags=["Stock Management"])


# ============================================================
# ADD STOCK (ENTRY)
# ============================================================

@router.post(
    "/add",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add stock to a product",
)
def add_stock(
        product_id: str = Query(..., description="Product UUID"),
        quantity: Decimal = Query(..., gt=0, description="Quantity to add (must be positive)"),
        notes: Optional[str] = Query(None, max_length=500, description="Optional notes"),
        db: Session = Depends(get_db),
        current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> dict:
    """
    Add stock to a product (reabastecimiento).

    **Required permissions:** Admin

    Creates an ENTRY movement and updates product stock.

    Args:
        product_id: Product UUID
        quantity: Amount to add (must be positive)
        notes: Optional notes about the entry
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Dictionary with updated product and created movement

    Raises:
        HTTPException 400: If quantity invalid or exceeds max stock
        HTTPException 404: If product not found
    """
    try:
        logger.info(
            f"Admin {current_user.username} adding {quantity} units to product {product_id}"
        )
        service = ProductService(db)
        product, movement = service.add_stock(product_id, quantity, notes)

        logger.info(f"Stock added successfully: {product_id}")
        return {
            "product": product,
            "movement": movement
        }
    except ValueError as e:
        logger.warning(f"Validation error adding stock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding stock: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add stock"
        )


# ============================================================
# REMOVE STOCK (EXIT)
# ============================================================

@router.post(
    "/remove",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Remove stock from a product",
)
def remove_stock(
        product_id: str = Query(..., description="Product UUID"),
        quantity: Decimal = Query(..., gt=0, description="Quantity to remove (must be positive)"),
        responsible: Optional[str] = Query(None, description="Username of person removing stock"),
        notes: Optional[str] = Query(None, max_length=500),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Remove stock from a product (venta/retiro).

    **Required permissions:** Employee or Admin

    Creates an EXIT movement with negative quantity.

    Args:
        product_id: Product UUID
        quantity: Amount to remove (must be positive)
        responsible: Username of person removing stock (defaults to current user)
        notes: Optional notes about the exit
        db: Database session
        current_user: Authenticated user

    Returns:
        Dictionary with updated product and created movement

    Raises:
        HTTPException 400: If insufficient stock or quantity invalid
        HTTPException 404: If product not found
    """
    try:
        responsible_user = responsible or current_user.username

        logger.info(
            f"User {current_user.username} removing {quantity} units from product {product_id}"
        )
        service = ProductService(db)
        product, movement = service.remove_stock(
            product_id,
            quantity,
            responsible_user,
            notes
        )

        logger.info(f"Stock removed successfully: {product_id}")
        return {
            "product": product,
            "movement": movement
        }
    except ValueError as e:
        logger.warning(f"Validation error removing stock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error removing stock: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove stock"
        )