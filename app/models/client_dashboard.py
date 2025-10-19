from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional
from datetime import date, datetime


class ClientBasicInfo(BaseModel):
    """Basic client information for dashboard."""
    id: UUID
    first_name: str
    last_name: str
    dni_type: str
    dni_number: str
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BiometricInfo(BaseModel):
    """Biometric information for dashboard."""
    type: Optional[str] = None
    thumbnail: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionInfo(BaseModel):
    """Subscription information for dashboard."""
    status: Optional[str] = None
    plan: Optional[str] = None
    end_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class ClientStats(BaseModel):
    """Client statistics for dashboard."""
    subscriptions: Optional[int] = None
    attendances: Optional[int] = None
    last_attendance: Optional[datetime] = None
    since: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClientDashboard(BaseModel):
    """Complete client dashboard information."""
    client: Optional[ClientBasicInfo] = None
    biometric: Optional[BiometricInfo] = None
    subscription: Optional[SubscriptionInfo] = None
    stats: Optional[ClientStats] = None

    model_config = ConfigDict(from_attributes=True)