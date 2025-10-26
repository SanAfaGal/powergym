"""
Product Repository Module

Handles all database operations for products.
Implements the Repository pattern for clean separation of concerns.
"""

from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models import ProductModel
from app.schemas.inventory import ProductCreate, ProductUpdate, StockStatusEnum


class ProductRepository:
    """
    Repository for Product model.

    Provides all CRUD operations and custom queries for products.
    Implements the repository pattern to abstract database operations.
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
    def create(self, product_data: ProductCreate) -> ProductModel:
        """
        Create a new product.

        Args:
            product_data: ProductCreate schema with product details

        Returns:
            Created ProductModel instance

        Raises:
            SQLAlchemy exceptions if validation fails
        """
        db_product = ProductModel(
            name=product_data.name,
            description=product_data.description,
            capacity_value=product_data.capacity_value,
            unit_type=product_data.unit_type,
            price=product_data.price,
            currency=product_data.currency,
            photo_url=product_data.photo_url,
            min_stock=product_data.min_stock,
            max_stock=product_data.max_stock,
            available_quantity=Decimal("0.00"),
            stock_status=StockStatusEnum.NORMAL,
        )
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    # ============================================================
    # READ OPERATIONS
    # ============================================================
    def get_by_id(self, product_id: str) -> Optional[ProductModel]:
        """
        Retrieve product by ID.

        Args:
            product_id: Product UUID

        Returns:
            ProductModel if found, None otherwise
        """
        return self.db.query(ProductModel).filter(
            ProductModel.id == product_id
        ).first()

    def get_all(
            self,
            skip: int = 0,
            limit: int = 100,
            active_only: bool = True
    ) -> list[ProductModel]:
        """
        Retrieve all products with pagination.

        Args:
            skip: Number of products to skip (pagination offset)
            limit: Maximum number of products to return
            active_only: If True, only return active products

        Returns:
            List of ProductModel instances
        """
        query = self.db.query(ProductModel)

        if active_only:
            query = query.filter(ProductModel.is_active == True)

        return query.offset(skip).limit(limit).all()

    def get_by_name(self, name: str) -> Optional[ProductModel]:
        """
        Retrieve product by name (case-insensitive).

        Args:
            name: Product name to search

        Returns:
            ProductModel if found, None otherwise
        """
        return self.db.query(ProductModel).filter(
            ProductModel.name.ilike(f"%{name}%")
        ).first()

    def get_count(self, active_only: bool = True) -> int:
        """
        Get total count of products.

        Args:
            active_only: If True, count only active products

        Returns:
            Total number of products
        """
        query = self.db.query(ProductModel)
        if active_only:
            query = query.filter(ProductModel.is_active == True)
        return query.count()

    # ============================================================
    # UPDATE OPERATIONS
    # ============================================================
    def update(
            self,
            product_id: str,
            product_data: ProductUpdate
    ) -> Optional[ProductModel]:
        """
        Update product with provided data.

        Args:
            product_id: Product UUID to update
            product_data: ProductUpdate schema with new data

        Returns:
            Updated ProductModel if found, None otherwise
        """
        db_product = self.get_by_id(product_id)
        if not db_product:
            return None

        # Update only provided fields (exclude None values)
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(db_product, field, value)

        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    def update_stock(
            self,
            product_id: str,
            quantity_delta: Decimal
    ) -> Optional[ProductModel]:
        """
        Update product stock quantity.

        Args:
            product_id: Product UUID
            quantity_delta: Amount to add/subtract (positive or negative)

        Returns:
            Updated ProductModel if found, None otherwise
        """
        db_product = self.get_by_id(product_id)
        if not db_product:
            return None

        db_product.available_quantity += quantity_delta
        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    def deactivate(self, product_id: str) -> Optional[ProductModel]:
        """
        Deactivate a product (soft delete).

        Args:
            product_id: Product UUID

        Returns:
            Updated ProductModel if found, None otherwise
        """
        db_product = self.get_by_id(product_id)
        if not db_product:
            return None

        db_product.is_active = False
        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    # ============================================================
    # DELETE OPERATIONS
    # ============================================================
    def delete(self, product_id: str) -> bool:
        """
        Hard delete a product (use deactivate for soft delete).

        Args:
            product_id: Product UUID

        Returns:
            True if deleted, False if not found
        """
        db_product = self.get_by_id(product_id)
        if not db_product:
            return False

        self.db.delete(db_product)
        self.db.commit()
        return True

    # ============================================================
    # FILTERED QUERIES
    # ============================================================
    def get_by_status(self, status: StockStatusEnum) -> list[ProductModel]:
        """
        Retrieve all products with specific stock status.

        Args:
            status: StockStatusEnum value

        Returns:
            List of ProductModel instances with given status
        """
        return self.db.query(ProductModel).filter(
            ProductModel.stock_status == status
        ).all()

    def get_low_stock_products(self) -> list[ProductModel]:
        """
        Retrieve all products with low stock.

        Returns:
            List of products where stock <= min_stock
        """
        return self.db.query(ProductModel).filter(
            and_(
                ProductModel.available_quantity < ProductModel.min_stock,
                ProductModel.is_active == True
            )
        ).all()

    def get_out_of_stock_products(self) -> list[ProductModel]:
        """
        Retrieve all products out of stock.

        Returns:
            List of products where stock = 0
        """
        return self.db.query(ProductModel).filter(
            and_(
                ProductModel.available_quantity == Decimal("0.00"),
                ProductModel.is_active == True
            )
        ).all()

    def get_overstock_products(self) -> list[ProductModel]:
        """
        Retrieve all products with overstock.

        Returns:
            List of products where stock > max_stock (if max_stock is set)
        """
        return self.db.query(ProductModel).filter(
            and_(
                ProductModel.max_stock.isnot(None),
                ProductModel.available_quantity > ProductModel.max_stock,
                ProductModel.is_active == True
            )
        ).all()

    def get_by_currency(self, currency: str) -> list[ProductModel]:
        """
        Retrieve all products with specific currency.

        Args:
            currency: Currency code (e.g., "COP", "USD")

        Returns:
            List of ProductModel instances with given currency
        """
        return self.db.query(ProductModel).filter(
            and_(
                ProductModel.currency == currency,
                ProductModel.is_active == True
            )
        ).all()

    def get_by_unit_type(self, unit_type: str) -> list[ProductModel]:
        """
        Retrieve all products with specific unit type.

        Args:
            unit_type: Unit type (e.g., "ml", "bottle", "can")

        Returns:
            List of ProductModel instances with given unit type
        """
        return self.db.query(ProductModel).filter(
            and_(
                ProductModel.unit_type == unit_type,
                ProductModel.is_active == True
            )
        ).all()

    # ============================================================
    # AGGREGATION OPERATIONS
    # ============================================================
    def get_total_inventory_value(self) -> Decimal:
        """
        Calculate total value of all active products in stock.

        Returns:
            Sum of (available_quantity * price) for all active products
        """
        products = self.db.query(ProductModel).filter(
            ProductModel.is_active == True
        ).all()

        total = sum(
            product.available_quantity * product.price
            for product in products
        )
        return Decimal(str(total))

    def get_inventory_stats(self) -> dict:
        """
        Get comprehensive inventory statistics.

        Returns:
            Dictionary with inventory metrics
        """
        active_products = self.db.query(ProductModel).filter(
            ProductModel.is_active == True
        ).all()

        return {
            "total_products": len(active_products),
            "low_stock_count": len(self.get_low_stock_products()),
            "out_of_stock_count": len(self.get_out_of_stock_products()),
            "overstock_count": len(self.get_overstock_products()),
            "total_inventory_value": self.get_total_inventory_value(),
            "total_units": sum(p.available_quantity for p in active_products),
        }

    # ============================================================
    # SEARCH OPERATIONS
    # ============================================================
    def search(
            self,
            query: str,
            skip: int = 0,
            limit: int = 100
    ) -> list[ProductModel]:
        """
        Search products by name or description.

        Args:
            query: Search term
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of matching ProductModel instances
        """
        return self.db.query(ProductModel).filter(
            and_(
                or_(
                    ProductModel.name.ilike(f"%{query}%"),
                    ProductModel.description.ilike(f"%{query}%")
                ),
                ProductModel.is_active == True
            )
        ).offset(skip).limit(limit).all()