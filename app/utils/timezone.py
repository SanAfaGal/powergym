# app/utils/timezone.py
from datetime import datetime, timezone
import pytz

TIMEZONE = pytz.timezone("America/Bogota")


def to_local(utc_dt: datetime) -> datetime:
    """Convierte UTC a local"""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(TIMEZONE)


def to_utc(local_dt: datetime) -> datetime:
    """Convierte local a UTC"""
    if local_dt.tzinfo is None:
        local_dt = TIMEZONE.localize(local_dt)
    return local_dt.astimezone(timezone.utc)


def get_date_range_utc(local_date: datetime) -> tuple[datetime, datetime]:
    """
    Convierte un día local a rango UTC.

    Ejemplo:
    - Input: 2025-10-25 (día local Bogotá)
    - Output: (2025-10-25 05:00:00 UTC, 2025-10-26 04:59:59.999999 UTC)
    """
    # Inicio del día local
    local_start = TIMEZONE.localize(
        datetime.combine(local_date.date(), datetime.min.time())
    )
    # Fin del día local
    local_end = TIMEZONE.localize(
        datetime.combine(local_date.date(), datetime.max.time())
    )

    # Convertir a UTC
    utc_start = local_start.astimezone(timezone.utc)
    utc_end = local_end.astimezone(timezone.utc)

    return utc_start, utc_end