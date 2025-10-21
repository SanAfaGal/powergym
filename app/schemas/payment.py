# app/models/payment.py

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional


class PaymentMethod(str, Enum):
    """Payment methods available"""
    CASH = "cash"
    QR = "qr"
    TRANSFER = "transfer"
    CARD = "card"


# ============= INPUT SCHEMAS =============

class PaymentCreateInput(BaseModel):
    """
    Input to create a payment.

    - amount: Exact payment amount (no tolerance)
    - payment_method: How the payment was made
    """
    amount: Decimal = Field(
        ...,
        description="Payment amount (exact value, no tolerance)",
        decimal_places=2,
        max_digits=10
    )
    payment_method: PaymentMethod = Field(
        ...,
        description="Payment method: cash, qr, transfer, card"
    )

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """Validate amount is positive and has valid decimal places"""
        if v <= 0:
            raise ValueError("Amount must be greater than 0")

        # Check decimal places
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount can have maximum 2 decimal places")

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "amount": "150.00",
                    "payment_method": "cash"
                },
                {
                    "amount": "75.50",
                    "payment_method": "qr"
                },
                {
                    "amount": "200.00",
                    "payment_method": "transfer"
                }
            ]
        }
    }


# ============= INTERNAL SCHEMAS =============

class PaymentCreate(BaseModel):
    """
    Internal schema for creating a payment.
    Used by the service layer.
    """
    subscription_id: UUID
    amount: Decimal
    payment_method: PaymentMethod


# ============= OUTPUT SCHEMAS =============

class Payment(BaseModel):
    """
    Payment response schema.
    What gets returned from the API.
    """
    id: UUID = Field(..., description="Payment ID")
    subscription_id: UUID = Field(..., description="Subscription ID")
    amount: Decimal = Field(..., description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    payment_date: datetime = Field(..., description="When the payment was made")
    meta_info: Optional[dict] = Field(
        default=None,
        description="Additional metadata"
    )

    class Config:
        from_attributes = True


class PaymentWithDebtInfo(BaseModel):
    """
    Extended payment response with debt information.
    Used after creating a payment to show remaining debt.
    """
    payment: Payment = Field(..., description="The payment that was created")
    remaining_debt: Optional[Decimal] = Field(
        default=None,
        description="Remaining debt (None if subscription is ACTIVE, $0 if fully paid)"
    )
    subscription_status: str = Field(
        ...,
        description="Subscription status after payment (active, pending_payment, etc)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "payment": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "subscription_id": "550e8400-e29b-41d4-a716-446655440000",
                        "amount": "100.00",
                        "payment_method": "cash",
                        "payment_date": "2025-10-20T15:30:00Z",
                        "meta_info": None
                    },
                    "remaining_debt": "50.00",
                    "subscription_status": "pending_payment"
                },
                {
                    "payment": {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "subscription_id": "550e8400-e29b-41d4-a716-446655440000",
                        "amount": "50.00",
                        "payment_method": "qr",
                        "payment_date": "2025-10-20T16:45:00Z",
                        "meta_info": None
                    },
                    "remaining_debt": "0.00",
                    "subscription_status": "active"
                }
            ]
        }
    }


class PaymentStats(BaseModel):
    """Payment statistics for a subscription or client"""
    subscription_id: Optional[UUID] = Field(None, description="Subscription ID (if stats are for a subscription)")
    client_id: Optional[UUID] = Field(None, description="Client ID (if stats are for a client)")
    total_payments: int = Field(..., description="Total number of payments")
    total_amount_paid: Decimal = Field(..., description="Total amount paid")
    remaining_debt: Decimal = Field(..., description="Remaining debt")
    last_payment_date: Optional[datetime] = Field(None, description="Last payment date")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subscription_id": "550e8400-e29b-41d4-a716-446655440000",
                    "client_id": None,
                    "total_payments": 3,
                    "total_amount_paid": "225.00",
                    "remaining_debt": "0.00",
                    "last_payment_date": "2025-10-20T16:45:00Z"
                },
                {
                    "subscription_id": None,
                    "client_id": "550e8400-e29b-41d4-a716-446655440001",
                    "total_payments": 5,
                    "total_amount_paid": "500.00",
                    "remaining_debt": "50.00",
                    "last_payment_date": "2025-10-20T16:45:00Z"
                }
            ]
        }
    }