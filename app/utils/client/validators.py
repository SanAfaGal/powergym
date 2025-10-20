from app.services.client_service import ClientService
from app.services.subscription_service import SubscriptionService
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status


class ClientValidator:
    """Validador reutilizable para clientes"""

    @staticmethod
    def get_or_404(db: Session, client_id: UUID) -> object:
        """Obtiene un cliente o lanza 404"""
        client = ClientService.get_client_by_id(db, client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        return client

    @staticmethod
    def verify_subscription_belongs_to_client(
            db: Session,
            subscription_id: UUID,
            client_id: UUID
    ) -> object:
        """Verifica que la subscripción pertenece al cliente"""
        subscription = SubscriptionService.get_subscription_by_id(db, subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscripción no encontrada"
            )

        if subscription.client_id != client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La subscripción no pertenece a este cliente"
            )

        return subscription

    @staticmethod
    def verify_dni_uniqueness(db: Session, dni: str, current_dni: str = None) -> None:
        """Verifica que el DNI sea único (excepto si es el mismo cliente)"""
        if dni and dni != current_dni:
            existing = ClientService.get_client_by_dni(db, dni)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe otro cliente con este número de documento"
                )
