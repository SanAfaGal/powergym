from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
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
    FACE = "face"
    FINGERPRINT = "fingerprint"

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

    biometrics = relationship("ClientBiometricModel", back_populates="client", cascade="all, delete-orphan")
    attendances = relationship("AttendanceModel", back_populates="client", cascade="all, delete-orphan")

class ClientBiometricModel(Base):
    __tablename__ = "client_biometrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(SQLEnum(BiometricTypeEnum, name="biometric_type"), nullable=False)
    compressed_data = Column(Text, nullable=False)
    thumbnail = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)
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
    biometric_type = Column(String, nullable=True)
    meta_info = Column(JSON, default={}, nullable=False)

    client = relationship("ClientModel", back_populates="attendances")
