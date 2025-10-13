from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional

class PaymentMethod(str, Enum):
    CASH = "cash"
    QR = "qr"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class PaymentBase(BaseModel):
    subscription_id: UUID
    amount: Decimal
    currency: str = "COP"
    payment_method: PaymentMethod

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Amount must be greater than zero')
        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3:
            raise ValueError('Currency must be a 3-letter code')
        return v.upper()

class PaymentCreate(PaymentBase):
    status: PaymentStatus = PaymentStatus.PENDING
    payment_date: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subscription_id": "123e4567-e89b-12d3-a456-426614174000",
                    "amount": 45000.00,
                    "currency": "COP",
                    "payment_method": "cash",
                    "status": "pending"
                }
            ]
        }
    }

class PaymentUpdate(BaseModel):
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None
    payment_date: Optional[datetime] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= 0:
            raise ValueError('Amount must be greater than zero')
        return v

class Payment(PaymentBase):
    id: UUID
    status: PaymentStatus
    payment_date: datetime
    created_at: datetime
    updated_at: datetime
    meta_info: dict = {}

    class Config:
        from_attributes = True
        use_enum_values = True

class PaymentInDB(Payment):
    pass
