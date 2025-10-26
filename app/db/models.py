from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, ForeignKey, JSON, Numeric, Integer, \
    CheckConstraint, DECIMAL, TIMESTAMP, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from pgvector.sqlalchemy import Vector

import uuid
from app.db.base import Base
from enum import Enum


class StockStatusEnum(str, Enum):
    NORMAL = "NORMAL"
    LOW_STOCK = "LOW_STOCK"
    STOCK_OUT = "STOCK_OUT"
    OVERSTOCK = "OVERSTOCK"


class InventoryMovementTypeEnum(str, Enum):
    """Type of inventory movement"""
    ENTRY = "ENTRY"
    EXIT = "EXIT"

class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class DocumentTypeEnum(str, Enum):
    CC = "CC"
    TI = "TI"
    CE = "CE"
    PP = "PP"


class GenderTypeEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class BiometricTypeEnum(str, Enum):
    FACE = "FACE"
    FINGERPRINT = "FINGERPRINT"


class DurationTypeEnum(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class SubscriptionStatusEnum(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING_PAYMENT = "pending_payment"
    SCHEDULED = "scheduled"
    CANCELED = "canceled"


class PaymentMethodEnum(str, Enum):
    CASH = "cash"
    QR = "qr"


class UserModel(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRoleEnum, name="user_role_enum"), nullable=False, default=UserRoleEnum.EMPLOYEE)
    disabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ClientModel(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    dni_type = Column(SQLEnum(DocumentTypeEnum, name="document_type_enum"), nullable=False)
    dni_number = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    second_last_name = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    alternative_phone = Column(String, nullable=True)
    birth_date = Column(Date, nullable=False)
    gender = Column(SQLEnum(GenderTypeEnum, name="gender_type_enum"), nullable=False)
    address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    meta_info = Column(JSON, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    biometrics = relationship("ClientBiometricModel", back_populates="client", cascade="all, delete-orphan")
    attendances = relationship("AttendanceModel", back_populates="client", cascade="all, delete-orphan")


class ClientBiometricModel(Base):
    __tablename__ = "client_biometrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SQLEnum(BiometricTypeEnum, name="biometric_type_enum"), nullable=False)
    thumbnail = Column(Text, nullable=True)
    embedding_vector = Column(Vector(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    meta_info = Column(JSON, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    client = relationship("ClientModel", back_populates="biometrics")


class AttendanceModel(Base):
    __tablename__ = "attendances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    check_in = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    meta_info = Column(JSON, default={}, nullable=False)

    client = relationship("ClientModel", back_populates="attendances")


class PlanModel(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(Text, nullable=False)
    slug = Column(Text, unique=True, index=True, nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="COP", nullable=False)
    duration_unit = Column(SQLEnum(DurationTypeEnum, name="duration_type_enum"), nullable=False)
    duration_count = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    meta_info = Column(JSON, default={}, nullable=False)

    subscriptions = relationship("SubscriptionModel", back_populates="plan")

    __table_args__ = (
        CheckConstraint("price >= 0", name="plans_price_check"),
    )


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SQLEnum(SubscriptionStatusEnum, name="subscription_status_enum"), nullable=False,
                    default=SubscriptionStatusEnum.PENDING_PAYMENT)
    cancellation_date = Column(Date, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    meta_info = Column(JSON, default={}, nullable=False)

    client = relationship("ClientModel", backref="subscriptions")
    plan = relationship("PlanModel", back_populates="subscriptions")
    payments = relationship("PaymentModel", back_populates="subscription", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="subscriptions_dates_check"),
    )


class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False,
                             index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethodEnum, name="payment_method_enum"), nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    meta_info = Column(JSON, default={}, nullable=False)

    subscription = relationship("SubscriptionModel", back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount > 0", name="payments_amount_check"),
    )


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    capacity_value: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(10), nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Stock directamente aquí
    available_quantity: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=Decimal("0.00"))
    min_stock: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=Decimal("5.00"))
    max_stock: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2))

    stock_status: Mapped[StockStatusEnum] = mapped_column(
        SQLEnum(StockStatusEnum,
        name="stock_status_enum"),
        nullable=False,
        default=StockStatusEnum.NORMAL,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)
    meta_info: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)

    movements: Mapped[list["InventoryMovementModel"]] = relationship(back_populates="product",
                                                                     cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("price >= 0", name="check_product_price_positive"),
        CheckConstraint("available_quantity >= 0", name="check_product_quantity_positive"),
        CheckConstraint("min_stock <= max_stock OR max_stock IS NULL", name="check_product_min_max_stock"),
    )


class InventoryMovementModel(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    movement_type: Mapped[InventoryMovementTypeEnum] = mapped_column(
        SQLEnum(InventoryMovementTypeEnum,
                name="inventory_movement_enum"),
        nullable=False,
        index=True
    )
    quantity: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False
    )
    movement_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    responsible: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("users.username", ondelete="SET NULL"),
        index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Auditoría
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Metadatos
    meta_info: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False
    )

    # Relaciones
    product: Mapped["ProductModel"] = relationship(back_populates="movements")

    __table_args__ = (
        CheckConstraint(
            "(movement_type = 'ENTRY' AND quantity > 0) OR (movement_type = 'EXIT' AND quantity < 0)",
            name="check_movement_quantity"
        ),
    )

    def __repr__(self) -> str:
        return f"<InventoryMovement(id={self.id}, type={self.movement_type}, qty={self.quantity})>"
