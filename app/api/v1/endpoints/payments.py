from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.schemas.payment import PaymentCreate, Payment
from app.services.payment_service import PaymentService
from typing import List, Dict, Any
from app.api.dependencies import get_current_active_user
from uuid import UUID
from app.schemas.user import User
from decimal import Decimal

router = APIRouter()


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process a payment for a subscription.

    Business rules:
    - Payment amount cannot exceed pending balance
    - Partial payments are allowed
    - Advance payments are tracked for future periods
    - Subscription status is updated automatically
    - Only one active subscription per client is enforced
    """
    try:
        result = PaymentService.process_payment(db, payment)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/renewal", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def process_renewal_payment(
    current_subscription_id: UUID,
    payment_amount: Decimal,
    payment_method: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process a renewal payment for an active subscription.

    Creates a new subscription for the next period if:
    - Current subscription is within 7 days of expiration
    - Current subscription has expired
    - There's advance credit from overpayment
    """
    try:
        result = PaymentService.process_renewal_payment(
            db, current_subscription_id, payment_amount, payment_method
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{payment_id}", response_model=Payment)
def get_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific payment by ID.
    """
    payment = PaymentService.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.get("/subscription/{subscription_id}", response_model=List[Payment])
def get_payments_by_subscription(
    subscription_id: UUID,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all payments for a specific subscription.
    """
    try:
        payments = PaymentService.get_payments_by_subscription(db, subscription_id, limit, offset)
        return payments
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/subscription/{subscription_id}/summary", response_model=Dict[str, Any])
def get_subscription_payment_summary(
    subscription_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get payment summary for a subscription.

    Returns:
    - Total amount paid
    - Pending balance
    - Advance amount (if any)
    - Payment count
    - Subscription status
    """
    try:
        summary = PaymentService.get_subscription_payment_summary(db, subscription_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=List[Payment])
def list_payments(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all payments with pagination.
    """
    try:
        payments = PaymentService.list_all_payments(db, limit, offset)
        return payments
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
