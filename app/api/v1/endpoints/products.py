"""
Product Endpoints Module

FastAPI routes for product management.
"""

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
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> ProductResponse:
    """
    Create a new product.

    **Required permissions:** Admin

    Args:
        product_data: ProductCreate schema with product details
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Created ProductResponse

    Raises:
        HTTPException 400: If validation fails
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
)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProductResponse:
    """
    Retrieve a product by ID.

    Args:
        product_id: Product UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        ProductResponse

    Raises:
        HTTPException 404: If product not found
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

    Args:
        skip: Number of products to skip (default: 0)
        limit: Maximum products per page (default: 100, max: 100)
        active_only: If true, only return active products (default: true)
        db: Database session
        current_user: Authenticated user

    Returns:
        Dictionary with products list and total count
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

    Args:
        q: Search query (required)
        skip: Pagination offset
        limit: Maximum results
        db: Database session
        current_user: Authenticated user

    Returns:
        List of matching ProductResponse instances
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

    Only provided fields will be updated (partial update).

    Args:
        product_id: Product UUID
        product_data: ProductUpdate schema with updated fields
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Updated ProductResponse

    Raises:
        HTTPException 404: If product not found
        HTTPException 400: If validation fails
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

    Args:
        product_id: Product UUID
        db: Database session
        current_user: Authenticated admin user

    Raises:
        HTTPException 404: If product not found
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