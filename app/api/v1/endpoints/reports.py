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
)
def get_inventory_stats(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> dict:
    """
    Get comprehensive inventory statistics.

    **Required permissions:** Admin

    Returns:
        Dictionary with inventory metrics:
        - total_products: Total number of active products
        - low_stock_count: Products with low stock
        - out_of_stock_count: Products with zero stock
        - overstock_count: Products with overstock
        - total_inventory_value: Total value in stock
        - total_units: Total units in stock
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
)
def get_low_stock_alerts(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> list[ProductResponse]:
    """
    Get all products with low stock.

    **Required permissions:** Admin

    Returns:
        List of products where stock <= min_stock
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
)
def get_out_of_stock(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> list[ProductResponse]:
    """
    Get all products out of stock.

    **Required permissions:** Admin

    Returns:
        List of products with stock = 0
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
)
def get_overstock(
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> list[ProductResponse]:
    """
    Get all products with overstock.

    **Required permissions:** Admin

    Returns:
        List of products where stock > max_stock (if max_stock is set)
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
)
def get_product_history(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get complete movement history for a product.

    Args:
        product_id: Product UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Dictionary with movement history and statistics:
        - product_id: Product UUID
        - total_movements: Total number of movements
        - total_entries: Total quantity entered
        - total_exits: Total quantity exited
        - entries_count: Number of entry movements
        - exits_count: Number of exit movements
        - last_movement: Last recorded movement
        - recent_movements: Last 50 movements
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
)
def get_daily_sales(
    date: Optional[str] = Query(
        None,
        description="Date in YYYY-MM-DD format (default: today)"
    ),
    responsible: Optional[str] = Query(
        None,
        description="Filter by employee username"
    ),
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> dict:
    """
    Get daily sales report (EXIT movements only).

    **Required permissions:** Admin

    Args:
        date: Date for report (YYYY-MM-DD format, defaults to today)
        responsible: Optional username to filter by
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Dictionary with daily sales statistics:
        - date: Report date
        - responsible: Filtered employee (if specified)
        - total_units_sold: Total units sold
        - total_transactions: Number of transactions
        - movements: List of exit movements

    Raises:
        HTTPException 400: If date format invalid
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
    summary="Get daily sales breakdown by employee",
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

    Used at end-of-day to verify and collect from each employee.
    Shows exactly how much each employee should deliver.

    Args:
        date: Date for report (YYYY-MM-DD format, defaults to today)
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Dictionary with sales and amounts by employee:
        - date: Report date
        - total_employees: Number of employees with sales
        - sales_by_employee: {
            "employee_name": {
              "total_units": Number of units sold,
              "total_amount": Amount in currency (COP),
              "total_transactions": Number of sales,
              "movements": [Detailed movement list]
            }
          }

    Example response:
        {
          "date": "2025-10-25",
          "total_employees": 2,
          "sales_by_employee": {
            "juan": {
              "total_units": 50,
              "total_amount": 127500,
              "total_transactions": 20,
              "movements": [...]
            },
            "maria": {
              "total_units": 70,
              "total_amount": 185000,
              "total_transactions": 25,
              "movements": [...]
            }
          }
        }

    Raises:
        HTTPException 400: If date format invalid
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
)
def get_reconciliation_report(
    start_date: str = Query(
        ...,
        description="Start date in YYYY-MM-DD format"
    ),
    end_date: str = Query(
        ...,
        description="End date in YYYY-MM-DD format"
    ),
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
) -> dict:
    """
    Get reconciliation report for cash/stock verification.

    **Required permissions:** Admin

    Used to verify employee deliveries match sales records.
    Helps identify discrepancies between recorded sales and actual cash.

    Args:
        start_date: Report start date (YYYY-MM-DD format, required)
        end_date: Report end date (YYYY-MM-DD format, required)
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Dictionary with reconciliation data by employee:
        - period: {start, end}
        - reconciliation: {
            "employee_name": {
              "total_units_sold": Amount,
              "exit_count": Number of sales,
              "entries": Total entries,
              "movements": [Movement list]
            }
          }

    Raises:
        HTTPException 400: If date format invalid or start > end
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