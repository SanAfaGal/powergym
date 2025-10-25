from datetime import datetime
from typing import Optional
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AccessDenialReason(str, Enum):
    """Razones por las que se puede denegar el acceso a un cliente."""

    CLIENT_NOT_FOUND = "client_not_found"
    CLIENT_INACTIVE = "client_inactive"
    NO_SUBSCRIPTION = "no_subscription"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    ALREADY_CHECKED_IN = "already_checked_in"


class AttendanceBase(BaseModel):
    """Base schema con campos comunes."""
    client_id: UUID = Field(..., description="ID del cliente")
    meta_info: Optional[dict] = Field(
        default_factory=dict,
        description="Información adicional"
    )


class AttendanceCreate(AttendanceBase):
    """Schema para crear una asistencia."""
    pass


class AttendanceResponse(BaseModel):
    """Schema de respuesta para una asistencia."""
    id: UUID = Field(..., description="ID de la asistencia")
    client_id: UUID = Field(..., description="ID del cliente")
    check_in: datetime = Field(..., description="Hora de entrada")
    meta_info: dict = Field(
        default_factory=dict,
        description="Información adicional"
    )

    model_config = ConfigDict(from_attributes=True)


class AttendanceWithClientInfo(AttendanceResponse):
    """Schema con información adicional del cliente."""
    client_first_name: str = Field(..., description="Nombre del cliente")
    client_last_name: str = Field(..., description="Apellido del cliente")
    client_dni_number: str = Field(..., description="Cédula del cliente")


class CheckInResponse(BaseModel):
    """Respuesta detallada de check-in con validaciones."""
    success: bool = Field(..., description="Si el check-in fue exitoso")
    message: str = Field(..., description="Mensaje para el usuario")
    can_enter: bool = Field(..., description="Si puede entrar")
    attendance: Optional[AttendanceResponse] = Field(
        None,
        description="Datos de la asistencia creada"
    )
    client_info: Optional[dict] = Field(
        None,
        description="Información del cliente"
    )
    reason: Optional[str] = Field(
        None,
        description="Razón de denegación si aplica"
    )


class ValidateAccessResponse(BaseModel):
    """Respuesta de validación de acceso."""
    success: bool = Field(..., description="Si la validación fue exitosa")
    can_enter: bool = Field(..., description="Si puede entrar")
    client_id: Optional[UUID] = Field(None, description="ID del cliente")
    client_info: Optional[dict] = Field(None, description="Info del cliente")
    confidence: Optional[float] = Field(None, description="Confianza")
    subscription_status: Optional[str] = Field(None, description="Estado suscripción")
    subscription_end_date: Optional[datetime] = Field(None, description="Fin suscripción")
    reason: Optional[str] = Field(None, description="Razón de denegación")
    detail: Optional[str] = Field(None, description="Detalles")
