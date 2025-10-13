from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional

class DurationType(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class PlanBase(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Decimal
    currency: str = "COP"
    duration_unit: DurationType
    duration_count: int

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError('Price cannot be negative')
        return v

    @field_validator('duration_count')
    @classmethod
    def validate_duration_count(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('Duration count must be greater than zero')
        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3:
            raise ValueError('Currency must be a 3-letter code')
        return v.upper()

class PlanCreate(PlanBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Basic Plan",
                    "slug": "basic-plan",
                    "description": "A basic subscription plan",
                    "price": 50000.00,
                    "currency": "COP",
                    "duration_unit": "month",
                    "duration_count": 1
                }
            ]
        }
    }

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    duration_unit: Optional[DurationType] = None
    duration_count: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        return v

    @field_validator('duration_count')
    @classmethod
    def validate_duration_count(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError('Duration count must be greater than zero')
        return v

class Plan(PlanBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    meta_info: dict = {}

    class Config:
        from_attributes = True
        use_enum_values = True

class PlanInDB(Plan):
    pass
