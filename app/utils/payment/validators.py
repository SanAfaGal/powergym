# app/utils/payment/validators.py

from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException, status
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.payment_repository import PaymentRepository
from app.db.models import SubscriptionStatusEnum, PaymentMethodEnum
import logging

logger = logging.getLogger(__name__)


class PaymentValidator:
    """Payment validation helpers"""

    @staticmethod
    def validate_subscription_exists(db: Session, subscription_id: UUID):
        """
        Validate subscription exists.

        Args:
            db: Database session
            subscription_id: Subscription UUID

        Raises:
            HTTPException 404 if subscription not found

        Returns:
            SubscriptionModel
        """
        subscription = SubscriptionRepository.get_by_id(db, subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        return subscription

    @staticmethod
    def validate_subscription_can_receive_payment(subscription):
        """
        Validate subscription can receive payments.

        Allowed statuses: ACTIVE, PENDING_PAYMENT, SCHEDULED
        Not allowed: CANCELED, EXPIRED

        Args:
            subscription: SubscriptionModel

        Raises:
            HTTPException 400 if subscription cannot receive payment
        """
        allowed_statuses = [
            SubscriptionStatusEnum.PENDING_PAYMENT,
            SubscriptionStatusEnum.SCHEDULED
        ]

        if subscription.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot create payment for subscription with status {subscription.status.value}"
            )

    @staticmethod
    def validate_payment_method_valid(payment_method: str):
        """
        Validate payment method is valid.

        Args:
            payment_method: Payment method value

        Raises:
            HTTPException 400 if payment method invalid
        """
        valid_methods = [method.value for method in PaymentMethodEnum]
        if payment_method not in valid_methods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payment method. Allowed: {', '.join(valid_methods)}"
            )

    @staticmethod
    def validate_amount_is_positive(amount: Decimal):
        """
        Validate amount is positive.

        Args:
            amount: Payment amount

        Raises:
            HTTPException 400 if amount <= 0
        """
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than 0"
            )

    @staticmethod
    def validate_payment_amount(db: Session, amount: Decimal, subscription):
        """
        Validate payment amount is valid for subscription status.

        For PENDING_PAYMENT: amount must not exceed remaining debt
        For ACTIVE: amount can be any positive value (adelantado)
        For SCHEDULED: amount can be any positive value (adelantado)

        Args:
            db: Database session
            amount: Payment amount
            subscription: SubscriptionModel

        Raises:
            HTTPException 400 if amount exceeds remaining debt (for PENDING_PAYMENT)
        """
        plan_price = Decimal(str(subscription.plan.price))

        if subscription.status == SubscriptionStatusEnum.PENDING_PAYMENT:
            # Calculate remaining debt
            total_paid = PaymentRepository.get_total_paid(db, subscription.id)
            remaining_debt = plan_price - total_paid

            if amount > remaining_debt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment amount ${amount} exceeds remaining debt ${remaining_debt}"
                )

        # For ACTIVE and SCHEDULED: any positive amount is allowed (adelantado)

    @staticmethod
    def validate_no_duplicate_payment_today(db: Session, subscription_id: UUID):
        """
        Prevent duplicate payments for the same subscription on the same day.

        Allows only one payment per subscription per day.

        Args:
            db: Database session
            subscription_id: Subscription UUID

        Raises:
            HTTPException 400 if payment already exists today
        """
        today_payment = PaymentRepository.get_by_subscription_today(db, subscription_id)
        if today_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment already exists for this subscription today"
            )