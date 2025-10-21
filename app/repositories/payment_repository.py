# app/repositories/payment_repository.py

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from app.db.models import PaymentModel, SubscriptionModel
import logging

logger = logging.getLogger(__name__)


class PaymentRepository:
    """Data access layer for payments"""

    @staticmethod
    def create(
            db: Session,
            subscription_id: UUID,
            amount: Decimal,
            payment_method: str
    ) -> PaymentModel:
        """
        Create a new payment.

        Args:
            db: Database session
            subscription_id: Subscription UUID
            amount: Payment amount
            payment_method: Payment method (cash, qr, transfer, card)

        Returns:
            PaymentModel: Created payment
        """
        try:
            payment = PaymentModel(
                subscription_id=subscription_id,
                amount=amount,
                payment_method=payment_method
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)

            logger.info(f"Payment created: {payment.id} for subscription {subscription_id}, amount: {amount}")
            return payment

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating payment: {str(e)}")
            raise

    @staticmethod
    def get_by_id(db: Session, payment_id: UUID) -> Optional[PaymentModel]:
        """
        Get payment by ID.

        Args:
            db: Database session
            payment_id: Payment UUID

        Returns:
            PaymentModel or None
        """
        return db.query(PaymentModel).filter(
            PaymentModel.id == payment_id
        ).first()

    @staticmethod
    def get_by_subscription(
            db: Session,
            subscription_id: UUID,
            limit: int = 100,
            offset: int = 0
    ) -> List[PaymentModel]:
        """
        Get all payments for a subscription.

        Args:
            db: Database session
            subscription_id: Subscription UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List[PaymentModel]: List of payments
        """
        return db.query(PaymentModel).filter(
            PaymentModel.subscription_id == subscription_id
        ).order_by(
            desc(PaymentModel.payment_date)
        ).limit(limit).offset(offset).all()

    @staticmethod
    def get_total_paid(db: Session, subscription_id: UUID) -> Decimal:
        """
        Get total amount paid for a subscription.

        Args:
            db: Database session
            subscription_id: Subscription UUID

        Returns:
            Decimal: Sum of all payment amounts
        """
        total = db.query(func.sum(PaymentModel.amount)).filter(
            PaymentModel.subscription_id == subscription_id
        ).scalar()

        return Decimal(str(total)) if total else Decimal('0.00')

    @staticmethod
    def get_by_subscription_today(db: Session, subscription_id: UUID) -> Optional[PaymentModel]:
        """
        Get payment for subscription created today.

        Used to prevent duplicate payments in the same day.

        Args:
            db: Database session
            subscription_id: Subscription UUID

        Returns:
            PaymentModel or None
        """
        today = date.today()

        return db.query(PaymentModel).filter(
            and_(
                PaymentModel.subscription_id == subscription_id,
                func.date(PaymentModel.payment_date) == today
            )
        ).first()

    @staticmethod
    def get_payments_by_client(
            db: Session,
            client_id: UUID,
            limit: int = 100,
            offset: int = 0
    ) -> List[PaymentModel]:
        """
        Get all payments made by a client (through subscriptions).

        Args:
            db: Database session
            client_id: Client UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List[PaymentModel]: List of all payments by client
        """
        return db.query(PaymentModel).join(
            SubscriptionModel,
            PaymentModel.subscription_id == SubscriptionModel.id
        ).filter(
            SubscriptionModel.client_id == client_id
        ).order_by(
            desc(PaymentModel.payment_date)
        ).limit(limit).offset(offset).all()

    @staticmethod
    def get_total_paid_by_client(db: Session, client_id: UUID) -> Decimal:
        """
        Get total amount paid by a client.

        Args:
            db: Database session
            client_id: Client UUID

        Returns:
            Decimal: Total amount paid by client
        """
        total = db.query(func.sum(PaymentModel.amount)).join(
            SubscriptionModel,
            PaymentModel.subscription_id == SubscriptionModel.id
        ).filter(
            SubscriptionModel.client_id == client_id
        ).scalar()

        return Decimal(str(total)) if total else Decimal('0.00')

    @staticmethod
    def count_by_subscription(db: Session, subscription_id: UUID) -> int:
        """
        Count total payments for a subscription.

        Args:
            db: Database session
            subscription_id: Subscription UUID

        Returns:
            int: Total count of payments
        """
        return db.query(PaymentModel).filter(
            PaymentModel.subscription_id == subscription_id
        ).count()

    @staticmethod
    def count_by_client(db: Session, client_id: UUID) -> int:
        """
        Count total payments made by a client.

        Args:
            db: Database session
            client_id: Client UUID

        Returns:
            int: Total count of payments
        """
        return db.query(PaymentModel).join(
            SubscriptionModel,
            PaymentModel.subscription_id == SubscriptionModel.id
        ).filter(
            SubscriptionModel.client_id == client_id
        ).count()

    @staticmethod
    def get_last_payment_date(db: Session, subscription_id: UUID) -> Optional[datetime]:
        """
        Get the last payment date for a subscription.

        Args:
            db: Database session
            subscription_id: Subscription UUID

        Returns:
            datetime or None: Last payment date
        """
        payment = db.query(PaymentModel).filter(
            PaymentModel.subscription_id == subscription_id
        ).order_by(desc(PaymentModel.payment_date)).first()

        return payment.payment_date if payment else None

    @staticmethod
    def get_last_payment_date_by_client(db: Session, client_id: UUID) -> Optional[datetime]:
        """
        Get the last payment date for a client.

        Args:
            db: Database session
            client_id: Client UUID

        Returns:
            datetime or None: Last payment date
        """
        payment = db.query(PaymentModel).join(
            SubscriptionModel,
            PaymentModel.subscription_id == SubscriptionModel.id
        ).filter(
            SubscriptionModel.client_id == client_id
        ).order_by(desc(PaymentModel.payment_date)).first()

        return payment.payment_date if payment else None