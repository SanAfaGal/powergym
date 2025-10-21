# app/api/routes/payments.py

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import logging

from app.schemas.payment import (
    Payment,
    PaymentCreateInput,
    PaymentWithDebtInfo,
    PaymentStats
)
from app.services.payment_service import PaymentService
from app.api.dependencies import get_current_active_user
from app.schemas.user import User
from app.db.session import get_db
from app.utils.payment.validators import PaymentValidator
from app.utils.payment.schema_builder import PaymentSchemaBuilder
from app.utils.client.validators import ClientValidator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["payments"])


# ============= PAYMENTS FOR SUBSCRIPTION =============
# All payment operations tied to a specific subscription

@router.post(
    "/subscriptions/{subscription_id}/payments",
    response_model=PaymentWithDebtInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Create payment for subscription",
    description="Create a payment for a specific subscription"
)
def create_payment(
    subscription_id: UUID,
    payment_input: PaymentCreateInput,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new payment for a subscription.

    Allowed for subscriptions in: ACTIVE, PENDING_PAYMENT, SCHEDULED
    - PENDING_PAYMENT: allows partial payments (abonos)
    - SCHEDULED: allows advance payments
    - If debt is fully paid, subscription becomes ACTIVE
    """
    subscription = PaymentValidator.validate_subscription_exists(db, subscription_id)
    PaymentValidator.validate_subscription_can_receive_payment(subscription)
    PaymentValidator.validate_payment_method_valid(payment_input.payment_method.value)
    PaymentValidator.validate_amount_is_positive(payment_input.amount)
    PaymentValidator.validate_payment_amount(db, payment_input.amount, subscription)
    PaymentValidator.validate_no_duplicate_payment_today(db, subscription_id)

    payment_data = PaymentSchemaBuilder.build_create(subscription_id, payment_input)
    result = PaymentService.create_payment(db, payment_data)

    return result


@router.get(
    "/subscriptions/{subscription_id}/payments",
    response_model=List[Payment],
    summary="List subscription payments",
    description="Get all payments for a specific subscription"
)
def get_subscription_payments(
    subscription_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all payments for a subscription"""
    PaymentValidator.validate_subscription_exists(db, subscription_id)

    payments = PaymentService.get_payments_by_subscription(db, subscription_id, limit, offset)
    return payments


@router.get(
    "/subscriptions/{subscription_id}/payments/stats",
    response_model=PaymentStats,
    summary="Get subscription payment stats",
    description="Get payment statistics for a subscription"
)
def get_subscription_payment_stats(
    subscription_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payment statistics for a subscription"""
    PaymentValidator.validate_subscription_exists(db, subscription_id)

    stats = PaymentService.get_subscription_payment_stats(db, subscription_id)
    return stats


# ============= PAYMENTS FOR CLIENT =============
# All payment operations across all subscriptions of a client

@router.get(
    "/clients/{client_id}/payments",
    response_model=List[Payment],
    summary="List client payments",
    description="Get all payments made by a client across all subscriptions"
)
def get_client_payments(
    client_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all payments made by a client"""
    ClientValidator.get_or_404(db, client_id)

    payments = PaymentService.get_payments_by_client(db, client_id, limit, offset)
    return payments


@router.get(
    "/clients/{client_id}/payments/stats",
    response_model=PaymentStats,
    summary="Get client payment stats",
    description="Get aggregated payment statistics for a client"
)
def get_client_payment_stats(
    client_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payment statistics for a client"""
    ClientValidator.get_or_404(db, client_id)

    stats = PaymentService.get_client_payment_stats(db, client_id)
    return stats