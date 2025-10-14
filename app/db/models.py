from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, ForeignKey, Enum as SQLEnum, JSON, Numeric, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.base import Base

class UserRoleEnum(str, enum.Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"

class DocumentTypeEnum(str, enum.Enum):
    CC = "CC"
    TI = "TI"
    CE = "CE"
    PP = "PP"

class GenderTypeEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class BiometricTypeEnum(str, enum.Enum):
    FACE = "FACE"
    FINGERPRINT = "fingerprint"

class DurationTypeEnum(str, enum.Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class SubscriptionStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING_PAYMENT = "pending_payment"
    CANCELED = "canceled"

class PaymentMethodEnum(str, enum.Enum):
    CASH = "cash"
    QR = "qr"

class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class UserModel(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRoleEnum, name="user_role"), nullable=False, default=UserRoleEnum.EMPLOYEE)
    disabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class ClientModel(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    dni_type = Column(SQLEnum(DocumentTypeEnum, name="document_type"), nullable=False)
    dni_number = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    second_last_name = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    alternative_phone = Column(String, nullable=True)
    birth_date = Column(Date, nullable=False)
    gender = Column(SQLEnum(GenderTypeEnum, name="gender_type"), nullable=False)
    address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    meta_info = Column(JSON, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # subscriptions = relationship("SubscriptionModel", back_populates="client")
    biometrics = relationship("ClientBiometricModel", back_populates="client", cascade="all, delete-orphan")
    attendances = relationship("AttendanceModel", back_populates="client", cascade="all, delete-orphan")

class ClientBiometricModel(Base):
    __tablename__ = "client_biometrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SQLEnum(BiometricTypeEnum, name="biometric_type"), nullable=False)
    thumbnail = Column(Text, nullable=True)
    embedding_vector = Column(Vector(128), nullable=True)
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
    duration_unit = Column(SQLEnum(DurationTypeEnum, name="duration_type"), nullable=False)
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
    status = Column(SQLEnum(SubscriptionStatusEnum, name="subscription_status"), nullable=False, default=SubscriptionStatusEnum.PENDING_PAYMENT)
    cancellation_date = Column(Date, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    meta_info = Column(JSON, default={}, nullable=False)

    client = relationship("ClientModel", backref="subscriptions")
    plan = relationship("PlanModel", back_populates="subscriptions")
    payments = relationship("PaymentModel", back_populates="subscription", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("end_date > start_date", name="subscriptions_dates_check"),
    )

class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethodEnum, name="payment_method"), nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    meta_info = Column(JSON, default={}, nullable=False)

    subscription = relationship("SubscriptionModel", back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount > 0", name="payments_amount_check"),
    )
