from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.subscription import Subscription, SubscriptionCreate, SubscriptionUpdate, SubscriptionStatus
from app.services.subscription_service import SubscriptionService
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.db.session import get_db
from uuid import UUID
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post(
    "/",
    response_model=Subscription,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subscription",
    description="Register a new subscription for a client with a specific plan.",
    responses={
        201: {
            "description": "Subscription successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "client_id": "123e4567-e89b-12d3-a456-426614174001",
                        "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                        "start_date": "2025-01-01",
                        "end_date": "2025-02-01",
                        "status": "pending_payment",
                        "created_at": "2025-10-13T10:30:00Z",
                        "updated_at": "2025-10-13T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Client or plan not found, or plan is inactive"},
        401: {"description": "Not authenticated"}
    }
)
def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new subscription for a client.
    """
    try:
        subscription = SubscriptionService.create_subscription(db, subscription_data)
        return subscription
    except ValueError as e:
        error_message = str(e) if str(e) else "Validation error"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    except Exception as e:
        logger_message = str(e) if hasattr(e, '__str__') else repr(e)
        logger.error(f"Error creating subscription: {logger_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la suscripción"
        )


@router.get(
    "/",
    response_model=List[Subscription],
    summary="List all subscriptions",
    description="Retrieve a paginated list of all subscriptions.",
    responses={
        200: {
            "description": "List of subscriptions",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "client_id": "123e4567-e89b-12d3-a456-426614174001",
                            "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                            "start_date": "2025-01-01",
                            "end_date": "2025-02-01",
                            "status": "active",
                            "created_at": "2025-10-13T10:30:00Z",
                            "updated_at": "2025-10-13T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def list_subscriptions(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of all subscriptions.
    """
    subscriptions = SubscriptionService.list_all_subscriptions(
        db=db,
        limit=limit,
        offset=offset
    )
    return subscriptions


@router.get(
    "/client/{client_id}",
    response_model=List[Subscription],
    summary="Get subscriptions by client",
    description="Retrieve all subscriptions for a specific client.",
    responses={
        200: {
            "description": "List of client subscriptions",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "client_id": "123e4567-e89b-12d3-a456-426614174001",
                            "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                            "start_date": "2025-01-01",
                            "end_date": "2025-02-01",
                            "status": "active",
                            "created_at": "2025-10-13T10:30:00Z",
                            "updated_at": "2025-10-13T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def get_subscriptions_by_client(
    client_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all subscriptions for a specific client.
    """
    subscriptions = SubscriptionService.get_subscriptions_by_client(
        db=db,
        client_id=client_id,
        limit=limit,
        offset=offset
    )
    return subscriptions


@router.get(
    "/client/{client_id}/active",
    response_model=List[Subscription],
    summary="Get active subscriptions by client",
    description="Retrieve all active subscriptions for a specific client.",
    responses={
        200: {
            "description": "List of active client subscriptions",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "client_id": "123e4567-e89b-12d3-a456-426614174001",
                            "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                            "start_date": "2025-01-01",
                            "end_date": "2025-02-01",
                            "status": "active",
                            "created_at": "2025-10-13T10:30:00Z",
                            "updated_at": "2025-10-13T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def get_active_subscriptions_by_client(
    client_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all active subscriptions for a specific client.
    """
    subscriptions = SubscriptionService.get_active_subscriptions_by_client(
        db=db,
        client_id=client_id
    )
    return subscriptions


@router.get(
    "/plan/{plan_id}",
    response_model=List[Subscription],
    summary="Get subscriptions by plan",
    description="Retrieve all subscriptions for a specific plan.",
    responses={
        200: {
            "description": "List of plan subscriptions",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "client_id": "123e4567-e89b-12d3-a456-426614174001",
                            "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                            "start_date": "2025-01-01",
                            "end_date": "2025-02-01",
                            "status": "active",
                            "created_at": "2025-10-13T10:30:00Z",
                            "updated_at": "2025-10-13T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def get_subscriptions_by_plan(
    plan_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all subscriptions for a specific plan.
    """
    subscriptions = SubscriptionService.get_subscriptions_by_plan(
        db=db,
        plan_id=plan_id,
        limit=limit,
        offset=offset
    )
    return subscriptions


@router.get(
    "/status/{status}",
    response_model=List[Subscription],
    summary="Get subscriptions by status",
    description="Retrieve all subscriptions with a specific status.",
    responses={
        200: {
            "description": "List of subscriptions with the specified status",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "client_id": "123e4567-e89b-12d3-a456-426614174001",
                            "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                            "start_date": "2025-01-01",
                            "end_date": "2025-02-01",
                            "status": "active",
                            "created_at": "2025-10-13T10:30:00Z",
                            "updated_at": "2025-10-13T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def get_subscriptions_by_status(
    status: SubscriptionStatus,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all subscriptions with a specific status.
    """
    subscriptions = SubscriptionService.get_subscriptions_by_status(
        db=db,
        status=status,
        limit=limit,
        offset=offset
    )
    return subscriptions


@router.get(
    "/{subscription_id}",
    response_model=Subscription,
    summary="Get subscription by ID",
    description="Retrieve a specific subscription by its ID.",
    responses={
        200: {
            "description": "Subscription found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "client_id": "123e4567-e89b-12d3-a456-426614174001",
                        "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                        "start_date": "2025-01-01",
                        "end_date": "2025-02-01",
                        "status": "active",
                        "created_at": "2025-10-13T10:30:00Z",
                        "updated_at": "2025-10-13T10:30:00Z"
                    }
                }
            }
        },
        404: {"description": "Subscription not found"},
        401: {"description": "Not authenticated"}
    }
)
def get_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific subscription by ID.
    """
    subscription = SubscriptionService.get_subscription_by_id(db, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )
    return subscription


@router.put(
    "/{subscription_id}",
    response_model=Subscription,
    summary="Update subscription",
    description="Update an existing subscription.",
    responses={
        200: {
            "description": "Subscription updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "client_id": "123e4567-e89b-12d3-a456-426614174001",
                        "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                        "start_date": "2025-01-01",
                        "end_date": "2025-03-01",
                        "status": "active",
                        "created_at": "2025-10-13T10:30:00Z",
                        "updated_at": "2025-10-13T12:00:00Z"
                    }
                }
            }
        },
        404: {"description": "Subscription not found"},
        401: {"description": "Not authenticated"}
    }
)
def update_subscription(
    subscription_id: UUID,
    subscription_update: SubscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a subscription.
    """
    existing_subscription = SubscriptionService.get_subscription_by_id(db, subscription_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )

    updated_subscription = SubscriptionService.update_subscription(
        db, subscription_id, subscription_update
    )
    if not updated_subscription:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la suscripción"
        )

    return updated_subscription


@router.post(
    "/{subscription_id}/cancel",
    response_model=Subscription,
    summary="Cancel subscription",
    description="Cancel an existing subscription.",
    responses={
        200: {
            "description": "Subscription canceled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "client_id": "123e4567-e89b-12d3-a456-426614174001",
                        "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                        "start_date": "2025-01-01",
                        "end_date": "2025-02-01",
                        "status": "canceled",
                        "cancellation_date": "2025-10-13",
                        "cancellation_reason": "Customer request",
                        "created_at": "2025-10-13T10:30:00Z",
                        "updated_at": "2025-10-13T14:00:00Z"
                    }
                }
            }
        },
        404: {"description": "Subscription not found"},
        401: {"description": "Not authenticated"}
    }
)
def cancel_subscription(
    subscription_id: UUID,
    cancellation_reason: Optional[str] = Query(None, description="Reason for cancellation"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a subscription.
    """
    existing_subscription = SubscriptionService.get_subscription_by_id(db, subscription_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )

    canceled_subscription = SubscriptionService.cancel_subscription(
        db, subscription_id, cancellation_reason
    )
    if not canceled_subscription:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cancelar la suscripción"
        )

    return canceled_subscription


@router.post(
    "/{subscription_id}/activate",
    response_model=Subscription,
    summary="Activate subscription",
    description="Activate a pending or expired subscription.",
    responses={
        200: {
            "description": "Subscription activated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "client_id": "123e4567-e89b-12d3-a456-426614174001",
                        "plan_id": "123e4567-e89b-12d3-a456-426614174002",
                        "start_date": "2025-01-01",
                        "end_date": "2025-02-01",
                        "status": "active",
                        "created_at": "2025-10-13T10:30:00Z",
                        "updated_at": "2025-10-13T15:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Cannot activate a canceled subscription"},
        404: {"description": "Subscription not found"},
        401: {"description": "Not authenticated"}
    }
)
def activate_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Activate a subscription.
    """
    existing_subscription = SubscriptionService.get_subscription_by_id(db, subscription_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )

    try:
        activated_subscription = SubscriptionService.activate_subscription(db, subscription_id)
        if not activated_subscription:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al activar la suscripción"
            )
        return activated_subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete subscription",
    description="Permanently delete a subscription from the database.",
    responses={
        204: {"description": "Subscription deleted successfully"},
        404: {"description": "Subscription not found"},
        401: {"description": "Not authenticated"}
    }
)
def delete_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Hard delete a subscription.
    """
    existing_subscription = SubscriptionService.get_subscription_by_id(db, subscription_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )

    success = SubscriptionService.delete_subscription(db, subscription_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar la suscripción"
        )

    return None
