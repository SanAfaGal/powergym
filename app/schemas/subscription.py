from pydantic import BaseModel, Field
from enum import Enum
from datetime import date, datetime
from uuid import UUID
from typing import Optional


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING_PAYMENT = "pending_payment"
    CANCELED = "canceled"
    SCHEDULED = "scheduled"


# ============= INPUT SCHEMAS =============

class SubscriptionCreateInput(BaseModel):
    """Input to create a subscription"""
    plan_id: UUID = Field(..., description="Plan ID")
    start_date: date = Field(..., description="Subscription start date")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "plan_id": "123e4567-e89b-12d3-a456-426614174001",
                "start_date": "2025-01-01"
            }]
        }
    }


class SubscriptionRenewInput(BaseModel):
    """Input to renew a subscription"""
    plan_id: Optional[UUID] = Field(
        default=None,
        description="Plan ID for renewal (defaults to same plan if not provided)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "plan_id": None
                },
                {
                    "plan_id": "123e4567-e89b-12d3-a456-426614174001"
                }
            ]
        }
    }


class SubscriptionCancelInput(BaseModel):
    """Input to cancel a subscription"""
    cancellation_reason: Optional[str] = Field(
        default=None,
        description="Reason for cancellation"
    )


# ============= INTERNAL SCHEMAS =============

class SubscriptionCreate(BaseModel):
    """Internal schema with client_id injected"""
    client_id: UUID
    plan_id: UUID
    start_date: date


class SubscriptionRenew(BaseModel):
    """Internal schema for renewal"""
    client_id: UUID
    subscription_id: UUID
    plan_id: Optional[UUID] = None


class SubscriptionCancel(BaseModel):
    """Internal schema for cancellation"""
    subscription_id: UUID
    cancellation_reason: Optional[str] = None


# ============= OUTPUT SCHEMAS =============

class Subscription(BaseModel):
    """Subscription response"""
    id: UUID
    client_id: UUID
    plan_id: UUID
    start_date: date
    end_date: date
    status: SubscriptionStatus
    cancellation_date: Optional[date] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    meta_info: Optional[dict] = None

    class Config:
        from_attributes = True
