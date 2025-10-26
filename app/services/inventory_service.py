"""
Inventory Services Module

Business logic layer for inventory operations.
Implements service pattern for clean separation of concerns.
Handles validation, orchestration, and business rules.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import ProductModel
from app.repositories.movement_repository import MovementRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    InventoryMovementCreate,
    InventoryMovementResponse,
    InventoryMovementTypeEnum,
)


class ProductService:
    """
    Service for product-related business logic.

    Handles:
    - Product creation, update, deletion
    - Stock validation and management
    - Business rule enforcement
    - Error handling and logging
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy session instance
        """
        self.db = db
        self.product_repo = ProductRepository(db)

    # ============================================================
    # CREATE OPERATIONS
    # ============================================================
    def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """
        Create a new product with validation.

        Validates:
        - Name is not empty
        - Price is non-negative
        - min_stock <= max_stock (if max_stock is provided)
        - Unit type is valid

        Args:
            product_data: ProductCreate schema with product details

        Returns:
            ProductResponse with created product

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraint violation
        """
        self._validate_product_data(product_data)

        try:
            db_product = self.product_repo.create(product_data)
            return ProductResponse.model_validate(db_product)
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create product: {str(e)}")

    # ============================================================
    # READ OPERATIONS
    # ============================================================
    def get_product(self, product_id: str) -> Optional[ProductResponse]:
        """
        Retrieve a product by ID.

        Args:
            product_id: Product UUID

        Returns:
            ProductResponse if found, None otherwise
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None
        return ProductResponse.model_validate(product)

    def get_all_products(
            self,
            skip: int = 0,
            limit: int = 100,
            active_only: bool = True
    ) -> tuple[list[ProductResponse], int]:
        """
        Retrieve all products with pagination.

        Args:
            skip: Number of products to skip
            limit: Maximum products to return (max 100)
            active_only: If True, only return active products

        Returns:
            Tuple of (products list, total count)
        """
        limit = min(limit, 100)  # Cap limit at 100

        products = self.product_repo.get_all(skip, limit, active_only)
        total = self.product_repo.get_count(active_only)

        return (
            [ProductResponse.model_validate(p) for p in products],
            total
        )

    def search_products(
            self,
            query: str,
            skip: int = 0,
            limit: int = 100
    ) -> list[ProductResponse]:
        """
        Search products by name or description.

        Args:
            query: Search term
            skip: Pagination offset
            limit: Maximum results (max 100)

        Returns:
            List of matching ProductResponse instances
        """
        limit = min(limit, 100)
        products = self.product_repo.search(query, skip, limit)
        return [ProductResponse.model_validate(p) for p in products]

    # ============================================================
    # UPDATE OPERATIONS
    # ============================================================
    def update_product(
            self,
            product_id: str,
            product_data: ProductUpdate
    ) -> Optional[ProductResponse]:
        """
        Update a product with validation.

        Validates:
        - Product exists
        - New min_stock <= max_stock (if both provided)
        - Price is non-negative

        Args:
            product_id: Product UUID
            product_data: ProductUpdate schema with new data

        Returns:
            Updated ProductResponse, None if product not found

        Raises:
            ValueError: If validation fails
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None

        self._validate_product_update(product, product_data)

        try:
            updated_product = self.product_repo.update(product_id, product_data)
            return ProductResponse.model_validate(updated_product)
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to update product: {str(e)}")

    def deactivate_product(self, product_id: str) -> Optional[ProductResponse]:
        """
        Deactivate a product (soft delete).

        Args:
            product_id: Product UUID

        Returns:
            Updated ProductResponse, None if not found
        """
        product = self.product_repo.deactivate(product_id)
        if not product:
            return None
        return ProductResponse.model_validate(product)

    # ============================================================
    # DELETE OPERATIONS
    # ============================================================
    def delete_product(self, product_id: str) -> bool:
        """
        Hard delete a product (use deactivate for soft delete).

        Warning: This cannot be undone. Consider using deactivate instead.

        Args:
            product_id: Product UUID

        Returns:
            True if deleted, False if not found
        """
        return self.product_repo.delete(product_id)

    # ============================================================
    # STOCK MANAGEMENT
    # ============================================================
    def add_stock(
            self,
            product_id: str,
            quantity: Decimal,
            notes: Optional[str] = None
    ) -> tuple[ProductResponse, InventoryMovementResponse]:
        """
        Add stock to a product (reabastecimiento).

        Creates an ENTRY movement and updates product stock.

        Args:
            product_id: Product UUID
            quantity: Amount to add (must be positive)
            notes: Optional notes about the entry

        Returns:
            Tuple of (updated ProductResponse, created MovementResponse)

        Raises:
            ValueError: If product not found or quantity invalid
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if product.max_stock and (product.available_quantity + quantity) > product.max_stock:
            raise ValueError(
                f"Adding {quantity} units would exceed max_stock ({product.max_stock})"
            )

        try:
            movement_data = InventoryMovementCreate(
                product_id=product_id,
                movement_type=InventoryMovementTypeEnum.ENTRY,
                quantity=quantity,
                notes=notes
            )

            movement_service = MovementService(self.db)
            movement = movement_service.create_movement(movement_data)

            updated_product = self.product_repo.get_by_id(product_id)
            return (
                ProductResponse.model_validate(updated_product),
                movement
            )
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to add stock: {str(e)}")

    def remove_stock(
            self,
            product_id: str,
            quantity: Decimal,
            responsible: Optional[str] = None,
            notes: Optional[str] = None
    ) -> tuple[ProductResponse, InventoryMovementResponse]:
        """
        Remove stock from a product (venta/retiro).

        Creates an EXIT movement with negative quantity.

        Args:
            product_id: Product UUID
            quantity: Amount to remove (must be positive, stored as negative)
            responsible: Username of person removing stock
            notes: Optional notes about the exit

        Returns:
            Tuple of (updated ProductResponse, created MovementResponse)

        Raises:
            ValueError: If product not found, insufficient stock, or quantity invalid
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if product.available_quantity < quantity:
            raise ValueError(
                f"Insufficient stock. Available: {product.available_quantity}, "
                f"Requested: {quantity}"
            )

        try:
            movement_data = InventoryMovementCreate(
                product_id=product_id,
                movement_type=InventoryMovementTypeEnum.EXIT,
                quantity=-quantity,  # Stored as negative
                responsible=responsible,
                notes=notes
            )

            movement_service = MovementService(self.db)
            movement = movement_service.create_movement(movement_data)

            updated_product = self.product_repo.get_by_id(product_id)
            return (
                ProductResponse.model_validate(updated_product),
                movement
            )
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to remove stock: {str(e)}")

    # ============================================================
    # INVENTORY REPORTS
    # ============================================================
    def get_inventory_stats(self) -> dict:
        """
        Get comprehensive inventory statistics.

        Returns:
            Dictionary with inventory metrics
        """
        return self.product_repo.get_inventory_stats()

    def get_low_stock_alerts(self) -> list[ProductResponse]:
        """
        Get all products with low stock.

        Returns:
            List of products with stock <= min_stock
        """
        products = self.product_repo.get_low_stock_products()
        return [ProductResponse.model_validate(p) for p in products]

    def get_out_of_stock_products(self) -> list[ProductResponse]:
        """
        Get all products out of stock.

        Returns:
            List of products with stock = 0
        """
        products = self.product_repo.get_out_of_stock_products()
        return [ProductResponse.model_validate(p) for p in products]

    def get_overstock_products(self) -> list[ProductResponse]:
        """
        Get all products with overstock.

        Returns:
            List of products with stock > max_stock
        """
        products = self.product_repo.get_overstock_products()
        return [ProductResponse.model_validate(p) for p in products]

    def get_total_inventory_value(self) -> Decimal:
        """
        Get total value of all products in stock.

        Returns:
            Sum of (available_quantity * price) for all products
        """
        return self.product_repo.get_total_inventory_value()

    # ============================================================
    # VALIDATION METHODS (PRIVATE)
    # ============================================================
    def _validate_product_data(self, product_data: ProductCreate) -> None:
        """
        Validate product creation data.

        Args:
            product_data: ProductCreate schema

        Raises:
            ValueError: If validation fails
        """
        if not product_data.name or not product_data.name.strip():
            raise ValueError("Product name cannot be empty")

        if product_data.price < 0:
            raise ValueError("Price cannot be negative")

        if product_data.min_stock < 0:
            raise ValueError("Min stock cannot be negative")

        if product_data.max_stock and product_data.max_stock < product_data.min_stock:
            raise ValueError("Max stock must be greater than or equal to min stock")

    def _validate_product_update(
            self,
            current_product: ProductModel,
            update_data: ProductUpdate
    ) -> None:
        """
        Validate product update data.

        Args:
            current_product: Current ProductModel instance
            update_data: ProductUpdate schema

        Raises:
            ValueError: If validation fails
        """
        if update_data.price is not None and update_data.price < 0:
            raise ValueError("Price cannot be negative")

        min_stock = update_data.min_stock or current_product.min_stock
        max_stock = update_data.max_stock or current_product.max_stock

        if max_stock and min_stock > max_stock:
            raise ValueError("Min stock cannot be greater than max stock")


class MovementService:
    """
    Service for inventory movement operations.

    Handles:
    - Movement creation and validation
    - Bulk operations
    - Movement history and reporting
    - Sales and reconciliation reports
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy session instance
        """
        self.db = db
        self.movement_repo = MovementRepository(db)

    # ============================================================
    # CREATE OPERATIONS
    # ============================================================
    def create_movement(
            self,
            movement_data: InventoryMovementCreate
    ) -> InventoryMovementResponse:
        """
        Create an inventory movement with validation.

        Validates:
        - Product exists
        - Quantity follows movement type rules

        Args:
            movement_data: InventoryMovementCreate schema

        Returns:
            Created InventoryMovementResponse

        Raises:
            ValueError: If validation fails
        """
        self._validate_movement_data(movement_data)

        try:
            db_movement = self.movement_repo.create(movement_data)
            return InventoryMovementResponse.model_validate(db_movement)
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create movement: {str(e)}")

    def create_bulk_movements(
            self,
            movements_data: list[InventoryMovementCreate]
    ) -> dict:
        """
        Create multiple movements in a transaction.

        Validates each movement before creation.
        If any movement fails, entire transaction is rolled back.

        Args:
            movements_data: List of InventoryMovementCreate schemas

        Returns:
            Dictionary with created movements and errors
        """
        if not movements_data:
            raise ValueError("At least one movement is required")

        for movement in movements_data:
            try:
                self._validate_movement_data(movement)
            except ValueError as e:
                raise ValueError(f"Validation error in bulk movements: {str(e)}")

        try:
            db_movements, errors = self.movement_repo.create_bulk(movements_data)

            return {
                "success": len(errors) == 0,
                "total": len(movements_data),
                "created": len(db_movements),
                "failed": len(errors),
                "movements": [
                    InventoryMovementResponse.model_validate(m)
                    for m in db_movements
                ],
                "errors": errors
            }
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create bulk movements: {str(e)}")

    # ============================================================
    # READ OPERATIONS
    # ============================================================
    def get_movement(self, movement_id: str) -> Optional[InventoryMovementResponse]:
        """
        Retrieve movement by ID.

        Args:
            movement_id: Movement UUID

        Returns:
            InventoryMovementResponse if found, None otherwise
        """
        movement = self.movement_repo.get_by_id(movement_id)
        if not movement:
            return None
        return InventoryMovementResponse.model_validate(movement)

    def get_all_movements(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> tuple[list[InventoryMovementResponse], int]:
        """
        Retrieve all movements with pagination.

        Args:
            skip: Pagination offset
            limit: Maximum results (capped at 100)

        Returns:
            Tuple of (movements list, total count)
        """
        limit = min(limit, 100)
        movements = self.movement_repo.get_all(skip, limit)
        total = self.movement_repo.get_count()

        return (
            [InventoryMovementResponse.model_validate(m) for m in movements],
            total
        )

    # ============================================================
    # PRODUCT HISTORY
    # ============================================================
    def get_product_history(self, product_id: str) -> dict:
        """
        Get complete movement history for a product.

        Args:
            product_id: Product UUID

        Returns:
            Dictionary with movement history and statistics
        """
        history = self.movement_repo.get_movement_history(product_id)
        return {
            "product_id": history["product_id"],
            "total_movements": history["total_movements"],
            "total_entries": history["total_entries"],
            "total_exits": history["total_exits"],
            "entries_count": history["total_entries_count"],
            "exits_count": history["total_exits_count"],
            "last_movement": (
                InventoryMovementResponse.model_validate(history["last_movement"])
                if history["last_movement"] else None
            ),
            "recent_movements": [
                InventoryMovementResponse.model_validate(m)
                for m in history["movements"]
            ]
        }

    # ============================================================
    # SALES REPORTS
    # ============================================================
    def get_daily_sales(
            self,
            date: Optional[datetime] = None,
            responsible: Optional[str] = None
    ) -> dict:
        """
        Get daily sales report (EXIT movements only).

        Args:
            date: Date for report (defaults to today)
            responsible: Optional username to filter by

        Returns:
            Dictionary with sales statistics
        """
        if date is None:
            date = datetime.now()

        sales_data = self.movement_repo.get_daily_sales(date, responsible)

        return {
            "date": sales_data["date"],
            "responsible": responsible,
            "total_units_sold": sales_data["total_units_sold"],
            "total_transactions": sales_data["total_transactions"],
            "movements": [
                InventoryMovementResponse.model_validate(m)
                for m in sales_data["movements"]
            ]
        }

    def get_daily_sales_by_employee(self, date: Optional[datetime] = None) -> dict:
        """
        Get daily sales breakdown by employee with monetary amounts.

        Used at end-of-day to verify how much each employee should deliver.
        Includes total units sold, monetary amounts, and transaction details.

        Args:
            date: Date for report (defaults to today)

        Returns:
            Dictionary with sales and amounts by employee
        """
        if date is None:
            date = datetime.now()

        sales_by_employee = self.movement_repo.get_sales_by_employee(date)

        return {
            "date": sales_by_employee["date"],
            "total_employees": sales_by_employee["total_employees"],
            "sales_by_employee": {
                employee: {
                    "total_units": sales["total_units"],
                    "total_amount": sales["total_amount"],
                    "total_transactions": sales["total_transactions"],
                    "movements": [
                        InventoryMovementResponse.model_validate(m)
                        for m in sales["movements"]
                    ]
                }
                for employee, sales in sales_by_employee["sales_by_employee"].items()
            }
        }

    # ============================================================
    # RECONCILIATION
    # ============================================================
    def get_reconciliation_report(
            self,
            start_date: datetime,
            end_date: datetime
    ) -> dict:
        """
        Get reconciliation report for cash/stock verification.

        Used to verify employee deliveries match sales records.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Dictionary with reconciliation data by employee
        """
        reconciliation = self.movement_repo.get_reconciliation_data(
            start_date,
            end_date
        )

        return {
            "period": reconciliation["period"],
            "reconciliation": {
                employee: {
                    "total_units_sold": data["total_exits"],
                    "exit_count": data["exit_count"],
                    "entries": data["entries"],
                    "movements": [
                        InventoryMovementResponse.model_validate(m)
                        for m in data["movements"]
                    ]
                }
                for employee, data in reconciliation["reconciliation"].items()
            }
        }

    # ============================================================
    # VALIDATION METHODS (PRIVATE)
    # ============================================================
    def _validate_movement_data(
            self,
            movement_data: InventoryMovementCreate
    ) -> None:
        """
        Validate movement data.

        Args:
            movement_data: InventoryMovementCreate schema

        Raises:
            ValueError: If validation fails
        """
        if movement_data.quantity == 0:
            raise ValueError("Quantity cannot be zero")

        if movement_data.movement_type == InventoryMovementTypeEnum.ENTRY:
            if movement_data.quantity < 0:
                raise ValueError("ENTRY movement quantity must be positive")
        elif movement_data.movement_type == InventoryMovementTypeEnum.EXIT:
            if movement_data.quantity > 0:
                raise ValueError("EXIT movement quantity must be negative")
        # ADJUSTMENT can be positive or negative
