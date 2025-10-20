from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from fastapi import HTTPException, status
from app.repositories.client_repository import ClientRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.db.models import SubscriptionStatusEnum


class SubscriptionValidator:
    """Subscription validation helpers"""

    @staticmethod
    def validate_client_exists(db: Session, client_id: UUID):
        """Validate client exists"""
        client = ClientRepository.get_by_id(db, client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        return client

    @staticmethod
    def validate_client_is_active(db: Session, client_id: UUID):
        """Validate client is active"""
        client = SubscriptionValidator.validate_client_exists(db, client_id)
        if not client.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client is inactive"
            )

    @staticmethod
    def validate_plan_exists(db: Session, plan_id: UUID):
        """Validate plan exists"""
        plan = PlanRepository.get_by_id(db, plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        return plan

    @staticmethod
    def validate_plan_is_active(plan):
        """Validate plan is active"""
        if not plan.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan is not active"
            )

    @staticmethod
    def validate_plan_duration(plan):
        """Validate plan has valid duration"""
        if plan.duration_count <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan has invalid duration"
            )

    @staticmethod
    def validate_start_date_not_in_past(start_date: date):
        """Validate start_date is today or in the future"""
        today = date.today()
        if start_date < today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Start date must be today or in the future. Today is {today}"
            )

    @staticmethod
    def validate_no_active_subscription(db: Session, client_id: UUID):
        """Validate client does NOT have an active subscription"""
        active_subs = SubscriptionRepository.get_active_by_client(db, client_id)
        if active_subs:
            active_sub = active_subs[0]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Client already has an active subscription until {active_sub.end_date}. Only one active subscription allowed"
            )

    @staticmethod
    def validate_subscription_exists(db: Session, subscription_id: UUID):
        """Validate subscription exists"""
        subscription = SubscriptionRepository.get_by_id(db, subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        return subscription

    @staticmethod
    def validate_subscription_belongs_to_client(
            db: Session,
            subscription_id: UUID,
            client_id: UUID
    ):
        """Validate subscription belongs to client"""
        subscription = SubscriptionValidator.validate_subscription_exists(db, subscription_id)
        if subscription.client_id != client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription does not belong to this client"
            )
        return subscription

    @staticmethod
    def validate_subscription_is_active(subscription):
        """Validate subscription is in ACTIVE status"""
        if subscription.status != SubscriptionStatusEnum.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is not active"
            )

    @staticmethod
    def validate_subscription_not_canceled(subscription):
        """Validate subscription is not canceled"""
        if subscription.status == SubscriptionStatusEnum.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot perform this action on a canceled subscription"
            )

    @staticmethod
    def validate_no_pending_renewal(db: Session, client_id: UUID):
        """
        Validate that client does NOT have a pending renewal.

        Prevents creating multiple renewals for the same subscription.
        A pending renewal is a SCHEDULED or PENDING_PAYMENT subscription.
        """
        pending_renewal = SubscriptionRepository.get_scheduled_by_client(db, client_id)
        if pending_renewal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Client already has a pending renewal scheduled starting on {pending_renewal.start_date}. Cancel it first if you want to create a new one"
            )
