from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from app.schemas.payment import (
    Payment,
    PaymentCreate,
    PaymentWithDebtInfo,
    PaymentStats
)
from app.repositories.payment_repository import PaymentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.db.models import SubscriptionStatusEnum
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """Business logic for payments"""

    @staticmethod
    def create_payment(db: Session, payment_data: PaymentCreate) -> PaymentWithDebtInfo:
        """Create a new payment for a subscription"""
        # Create payment
        payment_model = PaymentRepository.create(
            db=db,
            subscription_id=payment_data.subscription_id,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method.value
        )

        # Check if subscription needs status update
        subscription = SubscriptionRepository.get_by_id(db, payment_data.subscription_id)
        remaining_debt = None
        new_status = subscription.status.value

        if subscription.status == SubscriptionStatusEnum.PENDING_PAYMENT:
            total_paid = PaymentRepository.get_total_paid(db, subscription.id)
            plan_price = Decimal(str(subscription.plan.price))
            remaining_debt = plan_price - total_paid

            # If fully paid, activate
            if remaining_debt <= 0:
                SubscriptionRepository.update(
                    db=db,
                    subscription_id=subscription.id,
                    status=SubscriptionStatusEnum.ACTIVE
                )
                new_status = SubscriptionStatusEnum.ACTIVE.value
                remaining_debt = Decimal('0.00')
                logger.info(f"Subscription {subscription.id} activated after full payment")

        payment = Payment.from_orm(payment_model)

        return PaymentWithDebtInfo(
            payment=payment,
            remaining_debt=remaining_debt,
            subscription_status=new_status
        )

    @staticmethod
    def get_payments_by_subscription(
            db: Session,
            subscription_id: UUID,
            limit: int = 100,
            offset: int = 0
    ) -> List[Payment]:
        """Get all payments for a subscription"""
        payment_models = PaymentRepository.get_by_subscription(
            db,
            subscription_id,
            limit,
            offset
        )
        return [Payment.from_orm(p) for p in payment_models]

    @staticmethod
    def get_payments_by_client(
            db: Session,
            client_id: UUID,
            limit: int = 100,
            offset: int = 0
    ) -> List[Payment]:
        """Get all payments made by a client"""
        payment_models = PaymentRepository.get_payments_by_client(
            db,
            client_id,
            limit,
            offset
        )
        return [Payment.from_orm(p) for p in payment_models]

    @staticmethod
    def get_subscription_payment_stats(db: Session, subscription_id: UUID) -> PaymentStats:
        """Get payment statistics for a subscription"""
        subscription = SubscriptionRepository.get_by_id(db, subscription_id)
        total_paid = PaymentRepository.get_total_paid(db, subscription_id)
        plan_price = Decimal(str(subscription.plan.price))

        remaining_debt = Decimal('0.00')
        if subscription.status == SubscriptionStatusEnum.PENDING_PAYMENT:
            remaining_debt = max(plan_price - total_paid, Decimal('0.00'))

        total_payments = PaymentRepository.count_by_subscription(db, subscription_id)
        last_payment_date = PaymentRepository.get_last_payment_date(db, subscription_id)

        return PaymentStats(
            subscription_id=subscription_id,
            total_payments=total_payments,
            total_amount_paid=total_paid,
            remaining_debt=remaining_debt,
            last_payment_date=last_payment_date
        )

    @staticmethod
    def get_client_payment_stats(db: Session, client_id: UUID) -> PaymentStats:
        """Get payment statistics for a client"""
        total_paid = PaymentRepository.get_total_paid_by_client(db, client_id)
        total_payments = PaymentRepository.count_by_client(db, client_id)
        last_payment_date = PaymentRepository.get_last_payment_date_by_client(db, client_id)

        return PaymentStats(
            client_id=client_id,
            total_payments=total_payments,
            total_amount_paid=total_paid,
            remaining_debt=Decimal('0.00'),
            last_payment_date=last_payment_date
        )

