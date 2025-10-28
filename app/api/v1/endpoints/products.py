import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.schemas.user import User
from app.schemas.inventory import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)
from app.services.inventory_service import ProductService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])


# ============================================================
# CREATE OPERATIONS
# ============================================================

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    responses={
        201: {
            "description": "Product created successfully",
            "model": ProductResponse,
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Max stock must be greater than or equal to min stock"
                    }
                }
            }
        },
    }
)
def create_product(
        product_data: ProductCreate,
        db: Session = Depends(get_db),
        current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> ProductResponse:
    """
    Create a new product.

    **Required permissions:** Admin

    **Request Body:**
    - name: Product name (1-150 chars, required)
    - description: Optional product description (max 500 chars)
    - capacity_value: Capacity/volume (required, must be > 0)
    - unit_type: Unit of measurement like 'ml', 'bottle', 'can' (required)
    - price: Product price (required, >= 0)
    - currency: Currency code (default: 'COP')
    - photo_url: Optional product image URL
    - min_stock: Minimum stock threshold (default: 5.00)
    - max_stock: Maximum stock capacity (optional)

    **Response:**
    Returns the created ProductResponse with generated ID and timestamps.
    """
    try:
        logger.info(f"Admin {current_user.username} creating product: {product_data.name}")
        service = ProductService(db)
        product = service.create_product(product_data)
        logger.info(f"Product created successfully: {product.id}")
        return product
    except ValueError as e:
        logger.warning(f"Validation error creating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


# ============================================================
# READ OPERATIONS
# ============================================================

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    responses={
        200: {
            "description": "Product found",
            "model": ProductResponse,
        },
        404: {
            "description": "Product not found",
        },
    }
)
def get_product(
        product_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> ProductResponse:
    """
    Retrieve a product by ID.

    **Response Schema:**
    - id: Product unique identifier
    - name: Product name
    - description: Product description
    - capacity_value: Capacity value
    - unit_type: Unit type
    - price: Product price
    - currency: Currency code
    - photo_url: Product image URL
    - available_quantity: Current stock
    - min_stock: Minimum stock threshold
    - max_stock: Maximum stock capacity
    - stock_status: Current stock status (NORMAL, LOW, OUT_OF_STOCK, OVERSTOCK)
    - is_active: Whether product is active
    - created_at: Creation timestamp (UTC)
    - updated_at: Last update timestamp (UTC)
    """
    logger.debug(f"User {current_user.username} fetching product: {product_id}")
    service = ProductService(db)
    product = service.get_product(product_id)

    if not product:
        logger.warning(f"Product not found: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    return product


@router.get(
    "",
    response_model=dict,
    summary="List all products with pagination",
    responses={
        200: {
            "description": "List of products",
            "content": {
                "application/json": {
                    "example": {
                        "skip": 0,
                        "limit": 100,
                        "total": 5,
                        "items": [
                            {
                                "id": "uuid-1",
                                "name": "Coca Cola 350ml",
                                "description": "Soft drink",
                                "capacity_value": 350,
                                "unit_type": "ml",
                                "price": 2500,
                                "currency": "COP",
                                "photo_url": "https://example.com/coke.jpg",
                                "available_quantity": 50,
                                "min_stock": 10,
                                "max_stock": 200,
                                "stock_status": "NORMAL",
                                "is_active": True,
                                "created_at": "2025-01-15T10:30:00Z",
                                "updated_at": "2025-01-15T10:30:00Z"
                            }
                        ]
                    }
                }
            }
        }
    }
)
def list_products(
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(100, ge=1, le=100, description="Max items per page"),
        active_only: bool = Query(True, description="Only return active products"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    List all products with pagination.

    **Query Parameters:**
    - skip: Number of products to skip (default: 0)
    - limit: Maximum products per page (default: 100, max: 100)
    - active_only: If true, only return active products (default: true)

    **Response Schema:**
    - skip: Pagination offset used
    - limit: Pagination limit used
    - total: Total count of products matching filter
    - items: Array of ProductResponse objects
    """
    logger.debug(f"User {current_user.username} listing products: skip={skip}, limit={limit}")
    service = ProductService(db)
    products, total = service.get_all_products(skip, limit, active_only)

    return {
        "skip": skip,
        "limit": limit,
        "total": total,
        "items": products
    }


@router.get(
    "/search",
    response_model=list[ProductResponse],
    summary="Search products",
    responses={
        200: {
            "description": "Search results",
            "model": list[ProductResponse],
        },
    }
)
def search_products(
        q: str = Query(..., min_length=1, description="Search query"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> list[ProductResponse]:
    """
    Search products by name or description.

    **Query Parameters:**
    - q: Search query (required, min 1 character)
    - skip: Pagination offset
    - limit: Maximum results (max: 100)

    **Response Schema:**
    Array of ProductResponse objects matching the search query.
    """
    logger.debug(f"User {current_user.username} searching products: {q}")
    service = ProductService(db)
    return service.search_products(q, skip, limit)


# ============================================================
# UPDATE OPERATIONS
# ============================================================

@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
    responses={
        200: {
            "description": "Product updated successfully",
            "model": ProductResponse,
        },
        404: {
            "description": "Product not found",
        },
        400: {
            "description": "Validation error",
        }
    }
)
def update_product(
        product_id: str,
        product_data: ProductUpdate,
        db: Session = Depends(get_db),
        current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> ProductResponse:
    """
    Update a product.

    **Required permissions:** Admin

    **Request Body (all fields optional):**
    Only provided fields will be updated (partial update).

    **Response Schema:**
    Returns the updated ProductResponse with all fields.
    """
    try:
        logger.info(f"Admin {current_user.username} updating product: {product_id}")
        service = ProductService(db)
        product = service.update_product(product_id, product_data)

        if not product:
            logger.warning(f"Product not found for update: {product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )

        logger.info(f"Product updated successfully: {product_id}")
        return product
    except ValueError as e:
        logger.warning(f"Validation error updating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================
# DELETE OPERATIONS
# ============================================================

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a product",
    responses={
        204: {
            "description": "Product deactivated successfully",
        },
        404: {
            "description": "Product not found",
        }
    }
)
def deactivate_product(
        product_id: str,
        db: Session = Depends(get_db),
        current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> None:
    """
    Deactivate a product (soft delete).

    **Required permissions:** Admin

    The product is marked as inactive but not deleted from the database.

    **Response:**
    No content returned (204 status code).
    """
    logger.info(f"Admin {current_user.username} deactivating product: {product_id}")
    service = ProductService(db)
    product = service.deactivate_product(product_id)

    if not product:
        logger.warning(f"Product not found for deactivation: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    logger.info(f"Product deactivated successfully: {product_id}")