from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional

class PaymentMethod(str, Enum):
    CASH = "cash"
    QR = "qr"

class PaymentBase(BaseModel):
    subscription_id: UUID
    amount: Decimal
    payment_method: PaymentMethod

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Amount must be greater than zero')
        return v

class PaymentCreate(PaymentBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subscription_id": "123e4567-e89b-12d3-a456-426614174000",
                    "amount": 50000.00,
                    "payment_method": "cash"
                }
            ]
        }
    }

class Payment(PaymentBase):
    id: UUID
    payment_date: datetime
    meta_info: dict = {}

    class Config:
        from_attributes = True
        use_enum_values = True

class PaymentInDB(Payment):
    pass

class PaymentWithSubscription(Payment):
    subscription: Optional[dict] = None
