from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.db.models import StockStatusEnum, InventoryMovementTypeEnum
from app.utils.timezone import to_local


# ============================================================
# PRODUCT SCHEMAS
# ============================================================
class ProductCreate(BaseModel):
    """Schema para crear un producto"""
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    capacity_value: Decimal = Field(..., gt=0, decimal_places=2)
    unit_type: str = Field(..., min_length=1, max_length=10)
    price: Decimal = Field(..., ge=0, decimal_places=2)
    currency: str = Field(default="COP", min_length=3, max_length=3)
    photo_url: Optional[str] = Field(None, max_length=500)
    min_stock: Decimal = Field(default=Decimal("5.00"), ge=0, decimal_places=2)
    max_stock: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    """Schema para actualizar un producto"""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    capacity_value: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    unit_type: Optional[str] = Field(None, min_length=1, max_length=10)
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    photo_url: Optional[str] = Field(None, max_length=500)
    min_stock: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    max_stock: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    """Schema para retornar un producto"""
    id: str
    name: str
    description: Optional[str]
    capacity_value: Decimal
    unit_type: str
    price: Decimal
    currency: str
    photo_url: Optional[str]
    available_quantity: Decimal
    min_stock: Decimal
    max_stock: Optional[Decimal]
    stock_status: StockStatusEnum
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductResponse):
    """Schema detallado con movimientos"""
    movements: list["InventoryMovementResponse"] = []


# ============================================================
# INVENTORY MOVEMENT SCHEMAS
# ============================================================
class InventoryMovementCreate(BaseModel):
    """Schema para crear un movimiento de inventario"""
    product_id: str = Field(..., min_length=1)
    movement_type: InventoryMovementTypeEnum
    quantity: Decimal = Field(..., decimal_places=2)
    responsible: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)


class InventoryMovementResponse(BaseModel):
    """Schema para retornar un movimiento"""
    id: str
    product_id: str
    movement_type: InventoryMovementTypeEnum
    quantity: Decimal
    movement_date: datetime
    responsible: Optional[str]
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("movement_date", mode="after")
    @classmethod
    def convert_to_local(cls, v: datetime) -> datetime:
        """Convierte automáticamente a hora local"""
        return to_local(v)


class InventoryMovementDetailResponse(InventoryMovementResponse):
    """Schema detallado con info del producto"""
    product: Optional[ProductResponse] = None
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# REPORTS
# ============================================================
class StockReportResponse(BaseModel):
    """Reporte de stock de todos los productos"""
    total_products: int
    low_stock_count: int
    stock_out_count: int
    overstock_count: int
    products: list[ProductResponse]

    model_config = ConfigDict(from_attributes=True)

class DailySalesResponse(BaseModel):
    """Reporte de ventas del día"""
    date: str
    total_units_sold: Decimal
    total_amount: Decimal
    total_transactions: int
    products: list[dict]

    model_config = ConfigDict(from_attributes=True)

class InventoryHistoryResponse(BaseModel):
    """Historial de movimientos"""
    product_id: str
    product_name: str
    total_entries: int
    total_exits: int
    last_movement: Optional[InventoryMovementResponse]
    movements: list[InventoryMovementDetailResponse]

    model_config = ConfigDict(from_attributes=True)
