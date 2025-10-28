"""
Inventory Reports Endpoints Module

FastAPI routes for inventory analytics and reporting.
"""

import logging
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.schemas.user import User
from app.schemas.inventory import ProductResponse
from app.services.inventory_service import ProductService, MovementService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


# ============================================================
# INVENTORY STATISTICS ENDPOINTS
# ============================================================

@router.get(
    "/stats",
    response_model=dict,
    summary="Get inventory statistics",
    responses={
        200: {
            "description": "Inventory statistics",
            "content": {
                "application/json": {
                    "example": {
                        "total_products": 25,
                        "low_stock_count": 3,
                        "out_of_stock_count": 1,
                        "overstock_count": 2,
                        "total_inventory_value": 1250000,
                        "total_units": 850
                    }
                }
            }
        }
    }
)
def get_inventory_stats(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> dict:
    """
    Get comprehensive inventory statistics.

    **Required permissions:** Admin

    Returns overall inventory metrics and status overview.

    **Response Schema:**
    - total_products: Total number of active products in system
    - low_stock_count: Number of products with stock <= min_stock
    - out_of_stock_count: Number of products with stock = 0
    - overstock_count: Number of products with stock > max_stock
    - total_inventory_value: Total monetary value of all stock (quantity * price)
    - total_units: Total units in stock across all products

    **Use Case:** Dashboard overview, inventory health check
    """
    logger.info(f"Admin {current_user.username} requesting inventory statistics")
    service = ProductService(db)
    stats = service.get_inventory_stats()
    logger.debug(f"Inventory stats: {stats}")
    return stats


@router.get(
    "/low-stock",
    response_model=list[ProductResponse],
    summary="Get low stock products",
    responses={
        200: {
            "description": "Products with low stock",
            "model": list[ProductResponse],
        }
    }
)
def get_low_stock_alerts(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> list[ProductResponse]:
    """
    Get all products with low stock.

    **Required permissions:** Admin

    Returns list of products where current stock is at or below minimum threshold.

    **Response Schema:**
    Array of ProductResponse objects where available_quantity <= min_stock

    **Use Case:** Alerts for procurement, restocking decisions
    """
    logger.info(f"Admin {current_user.username} requesting low stock alerts")
    service = ProductService(db)
    products = service.get_low_stock_alerts()
    logger.debug(f"Found {len(products)} products with low stock")
    return products


@router.get(
    "/out-of-stock",
    response_model=list[ProductResponse],
    summary="Get out of stock products",
    responses={
        200: {
            "description": "Products with zero stock",
            "model": list[ProductResponse],
        }
    }
)
def get_out_of_stock(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> list[ProductResponse]:
    """
    Get all products out of stock.

    **Required permissions:** Admin

    Returns list of products with zero available quantity.

    **Response Schema:**
    Array of ProductResponse objects where available_quantity = 0

    **Use Case:** Critical alerts, urgent restocking, customer communication
    """
    logger.info(f"Admin {current_user.username} requesting out of stock products")
    service = ProductService(db)
    products = service.get_out_of_stock_products()
    logger.debug(f"Found {len(products)} out of stock products")
    return products


@router.get(
    "/overstock",
    response_model=list[ProductResponse],
    summary="Get overstock products",
    responses={
        200: {
            "description": "Products with overstock",
            "model": list[ProductResponse],
        }
    }
)
def get_overstock(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> list[ProductResponse]:
    """
    Get all products with overstock.

    **Required permissions:** Admin

    Returns list of products where stock exceeds maximum capacity.

    **Response Schema:**
    Array of ProductResponse objects where available_quantity > max_stock (only if max_stock is set)

    **Use Case:** Identify excess inventory, storage issues, waste prevention
    """
    logger.info(f"Admin {current_user.username} requesting overstock products")
    service = ProductService(db)
    products = service.get_overstock_products()
    logger.debug(f"Found {len(products)} overstock products")
    return products


# ============================================================
# PRODUCT HISTORY ENDPOINTS
# ============================================================

@router.get(
    "/products/{product_id}/history",
    response_model=dict,
    summary="Get product movement history",
    responses={
        200: {
            "description": "Product movement history",
            "content": {
                "application/json": {
                    "example": {
                        "product_id": "prod-uuid-1",
                        "total_movements": 45,
                        "total_entries": 500,
                        "total_exits": 320,
                        "entries_count": 12,
                        "exits_count": 33,
                        "last_movement": {
                            "id": "mov-uuid-1",
                            "product_id": "prod-uuid-1",
                            "movement_type": "EXIT",
                            "quantity": -15,
                            "movement_date": "2025-01-15T12:30:00Z",
                            "responsible": "juan",
                            "notes": "Sale"
                        },
                        "recent_movements": []
                    }
                }
            }
        }
    }
)
def get_product_history(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get complete movement history for a product.

    **Permissions:** Any authenticated user

    Returns detailed audit trail of all movements for a product.

    **Path Parameters:**
    - product_id: Product UUID (required)

    **Response Schema:**
    - product_id: The queried product UUID
    - total_movements: Total number of movements (entries + exits + adjustments)
    - total_entries: Sum of all quantities from ENTRY movements
    - total_exits: Sum of absolute values from EXIT movements
    - entries_count: Count of ENTRY movement records
    - exits_count: Count of EXIT movement records
    - last_movement: Most recent InventoryMovementResponse
    - recent_movements: Array of last 50 movements (newest first)

    **Use Case:** Product audit trail, historical analysis, reconciliation
    """
    logger.debug(f"User {current_user.username} fetching history for product: {product_id}")
    service = MovementService(db)
    history = service.get_product_history(product_id)
    logger.debug(f"Product history retrieved: {product_id}")
    return history


# ============================================================
# SALES REPORT ENDPOINTS
# ============================================================

@router.get(
    "/daily-sales",
    response_model=dict,
    summary="Get daily sales report",
    responses={
        200: {
            "description": "Daily sales statistics",
            "content": {
                "application/json": {
                    "example": {
                        "date": "2025-01-15",
                        "responsible": None,
                        "total_units_sold": 250,
                        "total_transactions": 45,
                        "movements": [
                            {
                                "id": "mov-uuid-1",
                                "product_id": "prod-uuid-1",
                                "movement_type": "EXIT",
                                "quantity": -15,
                                "movement_date": "2025-01-15T12:30:00Z",
                                "responsible": "juan",
                                "notes": None
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Invalid date format",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid date format. Use YYYY-MM-DD"}
                }
            }
        }
    }
)
def get_daily_sales(
    date: Optional[str] = Query(
        None,
        description="Date in YYYY-MM-DD format (default: today)"
    ),
    responsible: Optional[str] = Query(
        None,
        description="Filter by employee username (optional)"
    ),
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> dict:
    """
    Get daily sales report (EXIT movements only).

    **Required permissions:** Admin

    Generates sales report for a specific date with optional employee filtering.

    **Query Parameters:**
    - date: Report date in YYYY-MM-DD format (optional, defaults to today)
    - responsible: Filter by employee username (optional)

    **Response Schema:**
    - date: Report date (YYYY-MM-DD format)
    - responsible: Filtered employee if specified, None otherwise
    - total_units_sold: Total units sold on this date
    - total_transactions: Number of sale transactions
    - movements: Array of EXIT InventoryMovementResponse objects for the date

    **Use Case:** Daily sales verification, employee performance tracking, revenue reporting
    """
    try:
        report_date = datetime.fromisoformat(date) if date else None
    except ValueError:
        logger.warning(f"Invalid date format: {date}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    logger.info(
        f"Admin {current_user.username} requesting daily sales report: "
        f"date={date}, responsible={responsible}"
    )
    service = MovementService(db)
    sales = service.get_daily_sales(report_date, responsible)
    logger.debug(f"Daily sales report: {sales['total_units_sold']} units sold")
    return sales


@router.get(
    "/daily-sales-by-employee",
    response_model=dict,
    summary="Get daily sales breakdown by employee WITH MONETARY AMOUNTS",
    responses={
        200: {
            "description": "Daily sales breakdown by employee with amounts",
            "content": {
                "application/json": {
                    "example": {
                        "date": "2025-01-15",
                        "total_employees": 2,
                        "sales_by_employee": {
                            "juan": {
                                "total_units": 50,
                                "total_amount": 127500,
                                "total_transactions": 20,
                                "movements": [
                                    {
                                        "id": "mov-uuid-1",
                                        "product_id": "prod-uuid-1",
                                        "movement_type": "EXIT",
                                        "quantity": -5,
                                        "movement_date": "2025-01-15T10:30:00Z",
                                        "responsible": "juan",
                                        "notes": None
                                    }
                                ]
                            },
                            "maria": {
                                "total_units": 70,
                                "total_amount": 185000,
                                "total_transactions": 25,
                                "movements": []
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid date format",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid date format. Use YYYY-MM-DD"}
                }
            }
        }
    }
)
def get_daily_sales_by_employee(
    date: Optional[str] = Query(
        None,
        description="Date in YYYY-MM-DD format (default: today)"
    ),
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> dict:
    """
    Get daily sales breakdown by employee WITH MONETARY AMOUNTS.

    **Required permissions:** Admin

    **CRITICAL USE CASE:** End-of-day cash collection and verification.
    Shows exactly how much money each employee should deliver.

    **Query Parameters:**
    - date: Report date in YYYY-MM-DD format (optional, defaults to today)

    **Response Schema:**
    - date: Report date (YYYY-MM-DD format)
    - total_employees: Number of employees with sales that day
    - sales_by_employee: Dictionary keyed by employee username, each with:
      - total_units: Total units sold by employee
      - total_amount: Total monetary amount (quantity * product price)
      - total_transactions: Number of transactions
      - movements: Array of detailed EXIT movements

    **Employee Sales Object:**
    Each employee entry contains:
    ```
    {
        "total_units": 50,
        "total_amount": 127500,
        "total_transactions": 20,
        "movements": [InventoryMovementResponse objects]
    }
    ```

    **Use Case:**
    - End-of-day verification
    - Cash collection reconciliation
    - Employee accountability
    - Revenue tracking by staff member
    """
    try:
        report_date = datetime.fromisoformat(date) if date else None
    except ValueError:
        logger.warning(f"Invalid date format: {date}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    logger.info(
        f"Admin {current_user.username} requesting daily sales by employee: date={date}"
    )
    service = MovementService(db)
    sales = service.get_daily_sales_by_employee(report_date)
    logger.debug(f"Sales by employee: {sales['total_employees']} employees")
    return sales


# ============================================================
# RECONCILIATION ENDPOINTS
# ============================================================

@router.get(
    "/reconciliation",
    response_model=dict,
    summary="Get reconciliation report",
    responses={
        200: {
            "description": "Reconciliation report",
            "content": {
                "application/json": {
                    "example": {
                        "period": {
                            "start": "2025-01-10",
                            "end": "2025-01-15"
                        },
                        "reconciliation": {
                            "juan": {
                                "total_units_sold": 250,
                                "exit_count": 45,
                                "entries": 100,
                                "movements": [
                                    {
                                        "id": "mov-uuid-1",
                                        "product_id": "prod-uuid-1",
                                        "movement_type": "EXIT",
                                        "quantity": -5,
                                        "movement_date": "2025-01-15T10:30:00Z",
                                        "responsible": "juan",
                                        "notes": None
                                    }
                                ]
                            },
                            "maria": {
                                "total_units_sold": 180,
                                "exit_count": 32,
                                "entries": 50,
                                "movements": []
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid date format or range",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_format": {
                            "value": {"detail": "Invalid date format. Use YYYY-MM-DD"}
                        },
                        "invalid_range": {
                            "value": {"detail": "start_date must be before end_date"}
                        }
                    }
                }
            }
        }
    }
)
def get_reconciliation_report(
    start_date: str = Query(
        ...,
        description="Start date in YYYY-MM-DD format (required)"
    ),
    end_date: str = Query(
        ...,
        description="End date in YYYY-MM-DD format (required)"
    ),
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> dict:
    """
    Get reconciliation report for cash/stock verification.

    **Required permissions:** Admin

    **CRITICAL USE CASE:** Verify employee deliveries match sales records.
    Helps identify discrepancies between recorded sales and actual cash collected.

    **Query Parameters:**
    - start_date: Report period start date in YYYY-MM-DD format (required)
    - end_date: Report period end date in YYYY-MM-DD format (required)

    **Response Schema:**
    - period: Object with:
      - start: Start date (YYYY-MM-DD)
      - end: End date (YYYY-MM-DD)
    - reconciliation: Dictionary keyed by employee username, each containing:
      - total_units_sold: Total units sold during period
      - exit_count: Number of EXIT transactions
      - entries: Total units entered during period
      - movements: Array of all movements for employee in period

    **Employee Reconciliation Object:**
    ```
    {
        "total_units_sold": 250,
        "exit_count": 45,
        "entries": 100,
        "movements": [InventoryMovementResponse objects]
    }
    ```

    **Reconciliation Process:**
    1. Get total_amount from daily_sales_by_employee endpoint
    2. Compare with employee's actual cash collection
    3. Identify discrepancies
    4. Use movement history for audit trail

    **Use Cases:**
    - End-of-period cash reconciliation
    - Employee accountability verification
    - Fraud detection
    - Stock count verification
    - Financial audit trail

    **Error Cases:**
    - 400: Invalid date format or start_date > end_date
    - 401: Unauthorized (must be admin)
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        logger.warning(
            f"Invalid date format: start_date={start_date}, end_date={end_date}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    if start > end:
        logger.warning(f"Invalid date range: start={start_date}, end={end_date}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )

    logger.info(
        f"Admin {current_user.username} requesting reconciliation report: "
        f"period={start_date} to {end_date}"
    )
    service = MovementService(db)
    reconciliation = service.get_reconciliation_report(start, end)
    logger.debug(f"Reconciliation report generated for {len(reconciliation['reconciliation'])} employees")
    return reconciliation