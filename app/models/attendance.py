from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AttendanceBase(BaseModel):
    client_id: UUID
    biometric_type: Optional[str] = Field(None, pattern="^(face|fingerprint)$")
    meta_info: Optional[dict] = Field(default_factory=dict)


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceResponse(AttendanceBase):
    id: UUID
    check_in: datetime

    class Config:
        from_attributes = True


class AttendanceWithClientInfo(AttendanceResponse):
    client_first_name: str
    client_last_name: str
    client_dni_number: str
