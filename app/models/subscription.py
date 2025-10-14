from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import date, datetime
from uuid import UUID
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

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: date, info) -> date:
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError(f'End date ({v}) must be after start date ({info.data["start_date"]})')
        return v

class SubscriptionCreate(SubscriptionBase):
    status: SubscriptionStatus = SubscriptionStatus.PENDING_PAYMENT

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "client_id": "123e4567-e89b-12d3-a456-426614174000",
                    "plan_id": "123e4567-e89b-12d3-a456-426614174001",
                    "start_date": "2025-01-01",
                    "end_date": "2025-02-01",
                    "status": "pending_payment"
                }
            ]
        }
    }

class SubscriptionUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[SubscriptionStatus] = None
    cancellation_date: Optional[date] = None
    cancellation_reason: Optional[str] = None

class Subscription(SubscriptionBase):
    id: UUID
    status: SubscriptionStatus
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
