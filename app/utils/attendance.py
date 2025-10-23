from datetime import datetime, timedelta, date, time
from typing import Optional


class DateTimeUtil:
    """Utilidades para manejo de fechas."""

    @staticmethod
    def get_today_range() -> tuple[datetime, datetime]:
        """Obtener inicio y fin del día de hoy."""
        today = date.today()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)
        return start, end

    @staticmethod
    def is_valid_date_range(
            start_date: Optional[datetime],
            end_date: Optional[datetime]
    ) -> bool:
        """Validar que start_date sea menor que end_date."""
        if not start_date or not end_date:
            return True
        return start_date <= end_date


class AccessValidationUtil:
    """Utilidades para validación de acceso."""

    CONFIDENCE_THRESHOLD = 0.85

    @staticmethod
    def is_confidence_valid(confidence: float) -> bool:
        """Validar que la confianza facial sea suficiente."""
        return confidence >= AccessValidationUtil.CONFIDENCE_THRESHOLD

    @staticmethod
    def format_client_info(client) -> dict:
        """Formatear información del cliente."""
        return {
            "first_name": client.first_name,
            "last_name": client.last_name,
            "dni_number": client.dni_number
        }

    @staticmethod
    def format_subscription_info(subscription) -> dict:
        """Formatear información de suscripción."""
        return {
            "status": subscription.status,
            "end_date": subscription.end_date.isoformat(),
            "days_remaining": (subscription.end_date - datetime.now().date()).days
        }