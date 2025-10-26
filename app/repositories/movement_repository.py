"""
Inventory Movement Repository Module

Handles all database operations for inventory movements.
Implements the Repository pattern for clean separation of concerns.
All database dates are in UTC. Conversions happen automatically via utils.
"""

from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.db.models import InventoryMovementModel
from app.schemas.inventory import (
    InventoryMovementCreate,
    InventoryMovementTypeEnum,
)
from app.utils.timezone import get_date_range_utc


class MovementRepository:
    """
    Repository for InventoryMovement model.

    Provides all CRUD operations and custom queries for inventory movements.
    Implements the repository pattern to abstract database operations.
    Movements are immutable (write-once, read-many) records.

    All database dates are stored in UTC.
    Date conversions are handled by timezone utils automatically.
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy session instance
        """
        self.db = db

    # ============================================================
    # CREATE OPERATIONS
    # ============================================================

    def create(self, movement_data: InventoryMovementCreate) -> InventoryMovementModel:
        """
        Create a new inventory movement record.

        Movement records are immutable. If an error occurs, create an
        ADJUSTMENT movement instead of modifying the original.

        Args:
            movement_data: InventoryMovementCreate schema with movement details

        Returns:
            Created InventoryMovementModel instance

        Raises:
            SQLAlchemy exceptions if validation fails
        """
        db_movement = InventoryMovementModel(
            product_id=movement_data.product_id,
            movement_type=movement_data.movement_type,
            quantity=movement_data.quantity,
            responsible=movement_data.responsible,
            notes=movement_data.notes,
        )
        self.db.add(db_movement)
        self.db.commit()
        self.db.refresh(db_movement)
        return db_movement

    def create_bulk(
        self,
        movements_data: list[InventoryMovementCreate]
    ) -> tuple[list[InventoryMovementModel], list[dict]]:
        """
        Create multiple inventory movements in a transaction.

        If any movement fails, the entire transaction is rolled back.

        Args:
            movements_data: List of InventoryMovementCreate schemas

        Returns:
            Tuple of (created_movements, errors)
            - created_movements: List of successfully created movements
            - errors: List of dictionaries with error details
        """
        created_movements = []
        errors = []

        try:
            for idx, movement_data in enumerate(movements_data):
                try:
                    db_movement = InventoryMovementModel(
                        product_id=movement_data.product_id,
                        movement_type=movement_data.movement_type,
                        quantity=movement_data.quantity,
                        responsible=movement_data.responsible,
                        notes=movement_data.notes,
                    )
                    self.db.add(db_movement)
                    created_movements.append(db_movement)
                except Exception as e:
                    errors.append({
                        "index": idx,
                        "error": str(e),
                        "movement": movement_data.model_dump()
                    })

            if not errors:
                self.db.commit()
                for movement in created_movements:
                    self.db.refresh(movement)
            else:
                self.db.rollback()
                created_movements = []

            return created_movements, errors

        except Exception as e:
            self.db.rollback()
            return [], [{
                "index": None,
                "error": f"Transaction failed: {str(e)}",
                "movement": None
            }]

    # ============================================================
    # READ OPERATIONS
    # ============================================================

    def get_by_id(self, movement_id: str) -> Optional[InventoryMovementModel]:
        """
        Retrieve movement by ID.

        Args:
            movement_id: Movement UUID

        Returns:
            InventoryMovementModel if found, None otherwise
        """
        return self.db.query(InventoryMovementModel).filter(
            InventoryMovementModel.id == movement_id
        ).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[InventoryMovementModel]:
        """
        Retrieve all movements with pagination.

        Args:
            skip: Number of movements to skip (pagination offset)
            limit: Maximum number of movements to return

        Returns:
            List of InventoryMovementModel instances sorted by date (newest first)
        """
        return self.db.query(InventoryMovementModel).order_by(
            desc(InventoryMovementModel.movement_date)
        ).offset(skip).limit(limit).all()

    def get_count(self) -> int:
        """
        Get total count of movements.

        Returns:
            Total number of movements
        """
        return self.db.query(InventoryMovementModel).count()

    # ============================================================
    # FILTERED QUERIES
    # ============================================================

    def get_by_product(
        self,
        product_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[InventoryMovementModel]:
        """
        Retrieve all movements for a specific product.

        Args:
            product_id: Product UUID
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of InventoryMovementModel instances sorted by date (newest first)
        """
        return self.db.query(InventoryMovementModel).filter(
            InventoryMovementModel.product_id == product_id
        ).order_by(
            desc(InventoryMovementModel.movement_date)
        ).offset(skip).limit(limit).all()

    def get_by_responsible(
        self,
        username: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[InventoryMovementModel]:
        """
        Retrieve all movements by a specific user.

        Args:
            username: Username of responsible user
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of InventoryMovementModel instances
        """
        return self.db.query(InventoryMovementModel).filter(
            InventoryMovementModel.responsible == username
        ).order_by(
            desc(InventoryMovementModel.movement_date)
        ).offset(skip).limit(limit).all()

    def get_by_type(
        self,
        movement_type: InventoryMovementTypeEnum,
        skip: int = 0,
        limit: int = 100
    ) -> list[InventoryMovementModel]:
        """
        Retrieve all movements of a specific type.

        Args:
            movement_type: InventoryMovementTypeEnum (ENTRY, EXIT, ADJUSTMENT)
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of InventoryMovementModel instances
        """
        return self.db.query(InventoryMovementModel).filter(
            InventoryMovementModel.movement_type == movement_type
        ).order_by(
            desc(InventoryMovementModel.movement_date)
        ).offset(skip).limit(limit).all()

    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> list[InventoryMovementModel]:
        """
        Retrieve movements within a date range.

        Args:
            start_date: Start date in UTC (inclusive)
            end_date: End date in UTC (inclusive)
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of InventoryMovementModel instances
        """
        return self.db.query(InventoryMovementModel).filter(
            and_(
                InventoryMovementModel.movement_date >= start_date,
                InventoryMovementModel.movement_date <= end_date
            )
        ).order_by(
            desc(InventoryMovementModel.movement_date)
        ).offset(skip).limit(limit).all()

    def get_by_product_and_date_range(
        self,
        product_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> list[InventoryMovementModel]:
        """
        Retrieve movements for a product within a date range.

        Args:
            product_id: Product UUID
            start_date: Start date in UTC (inclusive)
            end_date: End date in UTC (inclusive)

        Returns:
            List of InventoryMovementModel instances
        """
        return self.db.query(InventoryMovementModel).filter(
            and_(
                InventoryMovementModel.product_id == product_id,
                InventoryMovementModel.movement_date >= start_date,
                InventoryMovementModel.movement_date <= end_date
            )
        ).order_by(
            desc(InventoryMovementModel.movement_date)
        ).all()

    # ============================================================
    # DATE-BASED QUERIES
    # ============================================================

    def get_today_movements(self) -> list[InventoryMovementModel]:
        """
        Retrieve all movements from today (in local timezone Bogotá).

        Returns:
            List of today's InventoryMovementModel instances
        """
        today_start_utc, today_end_utc = get_date_range_utc(datetime.now())
        return self.get_by_date_range(today_start_utc, today_end_utc)

    def get_today_exits(self) -> list[InventoryMovementModel]:
        """
        Retrieve all EXIT movements from today (sales).

        Returns:
            List of today's exit movements
        """
        today_movements = self.get_today_movements()
        return [
            m for m in today_movements
            if m.movement_type == InventoryMovementTypeEnum.EXIT
        ]

    def get_this_week_movements(self) -> list[InventoryMovementModel]:
        """
        Retrieve all movements from this week (Monday to today in local timezone).

        Returns:
            List of this week's movements
        """
        today = datetime.now()
        week_start_date = today - timedelta(days=today.weekday())

        week_start_utc, week_end_utc = get_date_range_utc(week_start_date)
        _, today_end_utc = get_date_range_utc(today)

        return self.get_by_date_range(week_start_utc, today_end_utc)

    def get_this_month_movements(self) -> list[InventoryMovementModel]:
        """
        Retrieve all movements from this month (1st to today in local timezone).

        Returns:
            List of this month's movements
        """
        today = datetime.now()
        month_start_date = datetime(today.year, today.month, 1)

        month_start_utc, _ = get_date_range_utc(month_start_date)
        _, today_end_utc = get_date_range_utc(today)

        return self.get_by_date_range(month_start_utc, today_end_utc)

    # ============================================================
    # AGGREGATION OPERATIONS
    # ============================================================

    def get_total_entries(self, product_id: str) -> Decimal:
        """
        Get total quantity of ENTRY movements for a product.

        Args:
            product_id: Product UUID

        Returns:
            Sum of all positive quantities from ENTRY movements
        """
        result = self.db.query(
            func.sum(InventoryMovementModel.quantity)
        ).filter(
            and_(
                InventoryMovementModel.product_id == product_id,
                InventoryMovementModel.movement_type == InventoryMovementTypeEnum.ENTRY
            )
        ).scalar()

        return Decimal(str(result or 0))

    def get_total_exits(self, product_id: str) -> Decimal:
        """
        Get total quantity of EXIT movements for a product (as positive number).

        Args:
            product_id: Product UUID

        Returns:
            Sum of absolute values from EXIT movements
        """
        result = self.db.query(
            func.sum(func.abs(InventoryMovementModel.quantity))
        ).filter(
            and_(
                InventoryMovementModel.product_id == product_id,
                InventoryMovementModel.movement_type == InventoryMovementTypeEnum.EXIT
            )
        ).scalar()

        return Decimal(str(result or 0))

    def get_movement_history(self, product_id: str) -> dict:
        """
        Get complete movement history for a product.

        Args:
            product_id: Product UUID

        Returns:
            Dictionary with movement statistics
        """
        all_movements = self.get_by_product(product_id, skip=0, limit=None)

        return {
            "product_id": product_id,
            "total_movements": len(all_movements),
            "total_entries": self.get_total_entries(product_id),
            "total_exits": self.get_total_exits(product_id),
            "total_entries_count": len([
                m for m in all_movements
                if m.movement_type == InventoryMovementTypeEnum.ENTRY
            ]),
            "total_exits_count": len([
                m for m in all_movements
                if m.movement_type == InventoryMovementTypeEnum.EXIT
            ]),
            "last_movement": all_movements[0] if all_movements else None,
            "movements": all_movements[:50],  # Return last 50
        }

    # ============================================================
    # SALES REPORT OPERATIONS
    # ============================================================

    def get_daily_sales(
        self,
        date: datetime,
        responsible: Optional[str] = None
    ) -> dict:
        """
        Get daily sales report (EXIT movements only).

        Converts local date to UTC range for database query.

        Args:
            date: Date in local timezone (Bogotá)
            responsible: Optional username to filter by

        Returns:
            Dictionary with sales statistics
        """
        # ✅ Convert local date to UTC range
        day_start_utc, day_end_utc = get_date_range_utc(date)

        query = self.db.query(InventoryMovementModel).filter(
            and_(
                InventoryMovementModel.movement_date >= day_start_utc,
                InventoryMovementModel.movement_date <= day_end_utc,
                InventoryMovementModel.movement_type == InventoryMovementTypeEnum.EXIT
            )
        )

        if responsible:
            query = query.filter(InventoryMovementModel.responsible == responsible)

        movements = query.all()

        total_units = sum(
            abs(m.quantity) for m in movements
        )
        total_transactions = len(movements)

        return {
            "date": date.date().isoformat(),
            "responsible": responsible,
            "total_units_sold": total_units,
            "total_transactions": total_transactions,
            "movements": movements,
        }

    def get_sales_by_employee(self, date: datetime) -> dict:
        """
        Get daily sales breakdown by employee with monetary amounts.

        Converts local date to UTC range for database query.

        Args:
            date: Date in local timezone (Bogotá)

        Returns:
            Dictionary with sales by employee including total amounts
        """
        # ✅ Convert local date to UTC range
        day_start_utc, day_end_utc = get_date_range_utc(date)

        query = self.db.query(InventoryMovementModel).filter(
            and_(
                InventoryMovementModel.movement_date >= day_start_utc,
                InventoryMovementModel.movement_date <= day_end_utc,
                InventoryMovementModel.movement_type == InventoryMovementTypeEnum.EXIT
            )
        )

        exit_movements = query.all()

        sales_by_employee = {}
        for movement in exit_movements:
            employee = movement.responsible or "Unknown"
            if employee not in sales_by_employee:
                sales_by_employee[employee] = {
                    "total_units": Decimal("0"),
                    "total_amount": Decimal("0"),
                    "total_transactions": 0,
                    "movements": []
                }

            # Calculate amount with product price
            quantity = abs(movement.quantity)
            product = movement.product
            amount = quantity * product.price

            sales_by_employee[employee]["total_units"] += quantity
            sales_by_employee[employee]["total_amount"] += amount
            sales_by_employee[employee]["total_transactions"] += 1
            sales_by_employee[employee]["movements"].append(movement)

        return {
            "date": date.date().isoformat(),
            "total_employees": len(sales_by_employee),
            "sales_by_employee": sales_by_employee,
        }

    # ============================================================
    # CONSISTENCY CHECK OPERATIONS
    # ============================================================

    def get_reconciliation_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        Get reconciliation data for cash/stock verification.

        Converts local dates to UTC range for database query.

        Args:
            start_date: Start date in local timezone (Bogotá)
            end_date: End date in local timezone (Bogotá)

        Returns:
            Dictionary with reconciliation data grouped by employee
        """
        # ✅ Convert local dates to UTC range
        range_start_utc, _ = get_date_range_utc(start_date)
        _, range_end_utc = get_date_range_utc(end_date)

        movements = self.get_by_date_range(range_start_utc, range_end_utc, limit=None)

        reconciliation = {}
        for movement in movements:
            employee = movement.responsible or "Unknown"

            if employee not in reconciliation:
                reconciliation[employee] = {
                    "total_exits": Decimal("0"),
                    "total_amount": Decimal("0"),
                    "exit_count": 0,
                    "entries": Decimal("0"),
                    "movements": []
                }

            if movement.movement_type == InventoryMovementTypeEnum.EXIT:
                quantity = abs(movement.quantity)
                amount = quantity * movement.product.price
                reconciliation[employee]["total_exits"] += quantity
                reconciliation[employee]["total_amount"] += amount
                reconciliation[employee]["exit_count"] += 1
            elif movement.movement_type == InventoryMovementTypeEnum.ENTRY:
                reconciliation[employee]["entries"] += movement.quantity

            reconciliation[employee]["movements"].append(movement)

        return {
            "period": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat()
            },
            "reconciliation": reconciliation,
        }