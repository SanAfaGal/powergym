from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.schemas.subscription import (
    Subscription,
    SubscriptionCreateInput,
    SubscriptionRenewInput,
    SubscriptionCancelInput
)
from app.services.subscription_service import SubscriptionService
from app.api.dependencies import get_current_active_user
from app.schemas.user import User
from app.db.session import get_db
from app.utils.subscription.schema_builder import SubscriptionSchemaBuilder
from app.utils.subscription.validators import SubscriptionValidator

router = APIRouter(prefix="/clients/{client_id}/subscriptions", tags=["subscriptions"])


@router.post(
    "/",
    response_model=Subscription,
    status_code=status.HTTP_201_CREATED,
    summary="Create subscription",
    description="Create a new subscription for a client"
)
def create_subscription(
        client_id: UUID,
        subscription_input: SubscriptionCreateInput,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Create a new subscription"""
    # Validations
    SubscriptionValidator.validate_client_exists(db, client_id)
    SubscriptionValidator.validate_client_is_active(db, client_id)

    plan = SubscriptionValidator.validate_plan_exists(db, subscription_input.plan_id)
    SubscriptionValidator.validate_plan_is_active(plan)
    SubscriptionValidator.validate_plan_duration(plan)

    SubscriptionValidator.validate_start_date_not_in_past(subscription_input.start_date)
    SubscriptionValidator.validate_no_active_subscription(db, client_id)

    # Build and create
    subscription_data = SubscriptionSchemaBuilder.build_create(client_id, subscription_input)
    subscription = SubscriptionService.create_subscription(db, subscription_data)

    return subscription


@router.get(
    "/active",
    response_model=Subscription,
    summary="Get active subscription",
    description="Get the active subscription for a client"
)
def get_active_subscription(
        client_id: UUID,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Get the active subscription for a client"""
    SubscriptionValidator.validate_client_exists(db, client_id)

    subscription = SubscriptionService.get_active_subscription_by_client(db, client_id)
    if not subscription:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client has no active subscription"
        )

    return subscription


@router.get(
    "/",
    response_model=List[Subscription],
    summary="Get client subscriptions",
    description="Get all subscriptions for a client"
)
def get_client_subscriptions(
        client_id: UUID,
        limit: int = 100,
        offset: int = 0,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Get all subscriptions for a client"""
    SubscriptionValidator.validate_client_exists(db, client_id)

    subscriptions = SubscriptionService.get_subscriptions_by_client(db, client_id, limit, offset)
    return subscriptions


@router.post(
    "/{subscription_id}/renew",
    response_model=Subscription,
    status_code=status.HTTP_201_CREATED,
    summary="Renew subscription",
    description="Renew a subscription. Creates a new subscription based on the old one"
)
def renew_subscription(
        client_id: UUID,
        subscription_id: UUID,
        renew_input: SubscriptionRenewInput = None,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Renew a subscription"""
    SubscriptionValidator.validate_client_exists(db, client_id)

    subscription = SubscriptionValidator.validate_subscription_belongs_to_client(
        db, subscription_id, client_id
    )
    SubscriptionValidator.validate_subscription_not_canceled(subscription)

    # Validate no pending renewal already exists
    SubscriptionValidator.validate_no_pending_renewal(db, client_id)

    # Validate plan if provided
    if renew_input and renew_input.plan_id:
        plan = SubscriptionValidator.validate_plan_exists(db, renew_input.plan_id)
        SubscriptionValidator.validate_plan_is_active(plan)
        SubscriptionValidator.validate_plan_duration(plan)

    # Build and renew
    renewal_data = SubscriptionSchemaBuilder.build_renew(
        client_id,
        subscription_id,
        renew_input or SubscriptionRenewInput()
    )
    renewed_subscription = SubscriptionService.renew_subscription(db, renewal_data)

    return renewed_subscription


@router.patch(
    "/{subscription_id}/cancel",
    response_model=Subscription,
    summary="Cancel subscription",
    description="Cancel an active subscription"
)
def cancel_subscription(
        client_id: UUID,
        subscription_id: UUID,
        cancel_input: SubscriptionCancelInput = None,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Cancel a subscription"""
    SubscriptionValidator.validate_client_exists(db, client_id)

    subscription = SubscriptionValidator.validate_subscription_belongs_to_client(
        db, subscription_id, client_id
    )
    SubscriptionValidator.validate_subscription_not_canceled(subscription)

    # Build and cancel
    cancel_data = SubscriptionSchemaBuilder.build_cancel(
        subscription_id,
        cancel_input or SubscriptionCancelInput()
    )
    canceled_subscription = SubscriptionService.cancel_subscription(db, cancel_data)

    return canceled_subscription
