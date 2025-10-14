from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING_PAYMENT = "pending_payment"
    CANCELED = "canceled"

class SubscriptionBase(BaseModel):
    client_id: UUID
    plan_id: UUID
    start_date: date
    end_date: date
    original_price: Decimal
    discount_amount: Decimal = Decimal("0")
    final_price: Decimal

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: date, info) -> date:
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @field_validator('original_price', 'final_price')
    @classmethod
    def validate_prices(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError('Price cannot be negative')
        return v

    @field_validator('discount_amount')
    @classmethod
    def validate_discount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError('Discount amount cannot be negative')
        return v

class SubscriptionCreate(SubscriptionBase):
    status: SubscriptionStatus = SubscriptionStatus.PENDING_PAYMENT
    auto_renew: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "client_id": "123e4567-e89b-12d3-a456-426614174000",
                    "plan_id": "123e4567-e89b-12d3-a456-426614174001",
                    "start_date": "2025-01-01",
                    "end_date": "2025-02-01",
                    "original_price": 50000.00,
                    "discount_amount": 5000.00,
                    "final_price": 45000.00,
                    "status": "pending_payment",
                    "auto_renew": False
                }
            ]
        }
    }

class SubscriptionUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    original_price: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    final_price: Optional[Decimal] = None
    status: Optional[SubscriptionStatus] = None
    auto_renew: Optional[bool] = None
    cancellation_date: Optional[date] = None
    cancellation_reason: Optional[str] = None

    @field_validator('original_price', 'final_price')
    @classmethod
    def validate_prices(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        return v

    @field_validator('discount_amount')
    @classmethod
    def validate_discount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError('Discount amount cannot be negative')
        return v

class Subscription(SubscriptionBase):
    id: UUID
    status: SubscriptionStatus
    auto_renew: bool
    cancellation_date: Optional[date] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    meta_info: dict = {}

    class Config:
        from_attributes = True
        use_enum_values = True

class SubscriptionInDB(Subscription):
    pass
