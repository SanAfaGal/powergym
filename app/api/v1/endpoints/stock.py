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
    responses={
        201: {
            "description": "Stock added successfully",
            "content": {
                "application/json": {
                    "example": {
                        "product": {
                            "id": "uuid-1",
                            "name": "Coca Cola 350ml",
                            "description": "Soft drink",
                            "capacity_value": 350,
                            "unit_type": "ml",
                            "price": 2500,
                            "currency": "COP",
                            "photo_url": "https://example.com/coke.jpg",
                            "available_quantity": 150,
                            "min_stock": 10,
                            "max_stock": 200,
                            "stock_status": "NORMAL",
                            "is_active": True,
                            "created_at": "2025-01-15T10:30:00Z",
                            "updated_at": "2025-01-15T11:45:00Z"
                        },
                        "movement": {
                            "id": "mov-uuid-1",
                            "product_id": "uuid-1",
                            "movement_type": "ENTRY",
                            "quantity": 100,
                            "movement_date": "2025-01-15T11:45:00Z",
                            "responsible": None,
                            "notes": "Stock replenishment from warehouse"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "examples": {
                        "insufficient_capacity": {
                            "value": {"detail": "Adding 500 units would exceed max_stock (200)"}
                        },
                        "invalid_quantity": {
                            "value": {"detail": "Quantity must be positive"}
                        },
                        "product_not_found": {
                            "value": {"detail": "Product uuid-xyz not found"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Product not found",
        },
    }
)
def add_stock(
        product_id: str = Query(..., description="Product UUID"),
        quantity: Decimal = Query(..., gt=0, description="Quantity to add (must be positive)"),
        notes: Optional[str] = Query(None, max_length=500, description="Optional notes about the entry"),
        db: Session = Depends(get_db),
        current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> dict:
    """
    Add stock to a product (reabastecimiento/replenishment).

    **Required permissions:** Admin

    Creates an ENTRY movement and updates product stock.

    **Query Parameters:**
    - product_id: Product UUID (required)
    - quantity: Amount to add in units (required, must be > 0)
    - notes: Optional notes about this stock entry (max 500 chars)

    **Response Schema:**
    Returns object with two fields:
    - product: Updated ProductResponse with new available_quantity
    - movement: Created InventoryMovementResponse with ENTRY type

    **Error Cases:**
    - 400: Quantity validation fails or would exceed max_stock
    - 404: Product not found
    - 500: Database or server error
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
    responses={
        201: {
            "description": "Stock removed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "product": {
                            "id": "uuid-1",
                            "name": "Coca Cola 350ml",
                            "description": "Soft drink",
                            "capacity_value": 350,
                            "unit_type": "ml",
                            "price": 2500,
                            "currency": "COP",
                            "photo_url": "https://example.com/coke.jpg",
                            "available_quantity": 85,
                            "min_stock": 10,
                            "max_stock": 200,
                            "stock_status": "NORMAL",
                            "is_active": True,
                            "created_at": "2025-01-15T10:30:00Z",
                            "updated_at": "2025-01-15T12:15:00Z"
                        },
                        "movement": {
                            "id": "mov-uuid-2",
                            "product_id": "uuid-1",
                            "movement_type": "EXIT",
                            "quantity": -15,
                            "movement_date": "2025-01-15T12:15:00Z",
                            "responsible": "juan",
                            "notes": "Sale to customer"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "examples": {
                        "insufficient_stock": {
                            "value": {"detail": "Insufficient stock. Available: 10, Requested: 50"}
                        },
                        "invalid_quantity": {
                            "value": {"detail": "Quantity must be positive"}
                        },
                        "product_not_found": {
                            "value": {"detail": "Product uuid-xyz not found"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Product not found",
        },
    }
)
def remove_stock(
        product_id: str = Query(..., description="Product UUID"),
        quantity: Decimal = Query(..., gt=0, description="Quantity to remove (must be positive)"),
        responsible: Optional[str] = Query(None, description="Username of person removing stock"),
        notes: Optional[str] = Query(None, max_length=500, description="Optional notes about the exit"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Remove stock from a product (venta/retiro - sale/withdrawal).

    **Required permissions:** Employee or Admin

    Creates an EXIT movement with negative quantity stored internally.

    **Query Parameters:**
    - product_id: Product UUID (required)
    - quantity: Amount to remove in units (required, must be > 0)
    - responsible: Username of person removing stock (optional, defaults to current user)
    - notes: Optional notes about this stock exit (max 500 chars)

    **Response Schema:**
    Returns object with two fields:
    - product: Updated ProductResponse with reduced available_quantity
    - movement: Created InventoryMovementResponse with EXIT type (quantity stored as negative)

    **Error Cases:**
    - 400: Insufficient stock or quantity validation fails
    - 404: Product not found
    - 500: Database or server error

    **Note:** The quantity in the movement response will be negative for EXIT movements.
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