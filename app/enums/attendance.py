from enum import Enum


class AccessDenialReason(str, Enum):
    """Razones por las que se deniega acceso."""

    # Errores de imagen
    NO_FACE_DETECTED = "no_face_detected"
    INVALID_IMAGE = "invalid_image"
    BLURRY_IMAGE = "blurry_image"

    # Reconocimiento facial
    FACE_NOT_RECOGNIZED = "face_not_recognized"
    LOW_CONFIDENCE = "low_confidence"

    # Cliente
    CLIENT_NOT_FOUND = "client_not_found"
    CLIENT_INACTIVE = "client_inactive"

    # Suscripción
    NO_SUBSCRIPTION = "no_subscription"
    SUBSCRIPTION_EXPIRED = "subscription_expired"

    # Pagos
    PENDING_PAYMENT = "pending_payment"


class DeviceType(str, Enum):
    """Tipos de dispositivos de acceso."""
    FACE_RECOGNITION = "face_recognition"
    RFID = "rfid"
    MANUAL = "manual"