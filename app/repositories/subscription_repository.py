# app/repositories/subscription_repository.py

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from uuid import UUID
from datetime import date
from typing import List, Optional
from app.db.models import SubscriptionModel, SubscriptionStatusEnum
import logging

logger = logging.getLogger(__name__)


class SubscriptionRepository:
    """Data access layer for subscriptions"""

    @staticmethod
    def create(
            db: Session,
            client_id: UUID,
            plan_id: UUID,
            start_date: date,
            end_date: date,
            status: SubscriptionStatusEnum = SubscriptionStatusEnum.PENDING_PAYMENT
    ) -> SubscriptionModel:
        """
        Create a new subscription.

        Args:
            db: Database session
            client_id: Client UUID
            plan_id: Plan UUID
            start_date: Subscription start date
            end_date: Subscription end date
            status: Initial status (default: PENDING_PAYMENT)

        Returns:
            SubscriptionModel: Created subscription
        """
        try:
            subscription = SubscriptionModel(
                client_id=client_id,
                plan_id=plan_id,
                start_date=start_date,
                end_date=end_date,
                status=status
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)

            logger.info(f"Subscription created: {subscription.id} for client {client_id}")
            return subscription

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating subscription: {str(e)}")
            raise

    @staticmethod
    def get_by_id(db: Session, subscription_id: UUID) -> Optional[SubscriptionModel]:
        """
        Get subscription by ID.

        Args:
            db: Database session
            subscription_id: Subscription UUID

        Returns:
            SubscriptionModel or None
        """
        return db.query(SubscriptionModel).filter(
            SubscriptionModel.id == subscription_id
        ).first()

    @staticmethod
    def get_active_by_client(db: Session, client_id: UUID) -> List[SubscriptionModel]:
        """
        Get active subscriptions for a client.

        Active means status is ACTIVE or PENDING_PAYMENT.
        Only one should exist at a time (enforced by business logic).

        Args:
            db: Database session
            client_id: Client UUID

        Returns:
            List[SubscriptionModel]: List of active subscriptions (should be max 1)
        """
        return db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.client_id == client_id,
                SubscriptionModel.status.in_([
                    SubscriptionStatusEnum.ACTIVE,
                    SubscriptionStatusEnum.PENDING_PAYMENT
                ])
            )
        ).order_by(desc(SubscriptionModel.created_at)).all()

    @staticmethod
    def get_scheduled_by_client(db: Session, client_id: UUID) -> Optional[SubscriptionModel]:
        """
        Get the next scheduled/pending renewal for a client.

        Returns the SCHEDULED or PENDING_PAYMENT subscription that represents
        a future renewal (not the current active one).

        This is used to prevent duplicate renewals.

        Args:
            db: Database session
            client_id: Client UUID

        Returns:
            SubscriptionModel or None: The pending renewal subscription
        """
        # Get all SCHEDULED and PENDING_PAYMENT subscriptions
        pending = db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.client_id == client_id,
                SubscriptionModel.status.in_([
                    SubscriptionStatusEnum.SCHEDULED,
                    SubscriptionStatusEnum.PENDING_PAYMENT
                ])
            )
        ).order_by(desc(SubscriptionModel.start_date)).all()

        if not pending:
            return None

        # Get the current active subscription (if any)
        active = db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.client_id == client_id,
                SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE
            )
        ).first()

        if not active:
            # No active subscription, return the first pending
            return pending[0]

        # Return pending subscriptions that start AFTER the active one ends
        for sub in pending:
            if sub.start_date > active.end_date:
                return sub

        # If no renewal found after active, return the oldest pending
        return pending[-1] if pending else None

    @staticmethod
    def get_by_client(
            db: Session,
            client_id: UUID,
            limit: int = 100,
            offset: int = 0
    ) -> List[SubscriptionModel]:
        """
        Get all subscriptions for a client with pagination.

        Args:
            db: Database session
            client_id: Client UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List[SubscriptionModel]: List of subscriptions
        """
        return db.query(SubscriptionModel).filter(
            SubscriptionModel.client_id == client_id
        ).order_by(
            desc(SubscriptionModel.created_at)
        ).limit(limit).offset(offset).all()

    @staticmethod
    def get_by_status(
            db: Session,
            status: SubscriptionStatusEnum,
            limit: int = 100,
            offset: int = 0
    ) -> List[SubscriptionModel]:
        """
        Get all subscriptions with a specific status.

        Args:
            db: Database session
            status: SubscriptionStatusEnum
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List[SubscriptionModel]: List of subscriptions
        """
        return db.query(SubscriptionModel).filter(
            SubscriptionModel.status == status
        ).order_by(
            desc(SubscriptionModel.created_at)
        ).limit(limit).offset(offset).all()

    @staticmethod
    def update(
            db: Session,
            subscription_id: UUID,
            **kwargs
    ) -> Optional[SubscriptionModel]:
        """
        Update subscription fields.

        Args:
            db: Database session
            subscription_id: Subscription UUID
            **kwargs: Fields to update (e.g., status=..., end_date=...)

        Returns:
            SubscriptionModel or None if not found
        """
        try:
            subscription = SubscriptionRepository.get_by_id(db, subscription_id)
            if not subscription:
                return None

            for key, value in kwargs.items():
                if hasattr(subscription, key):
                    setattr(subscription, key, value)

            db.commit()
            db.refresh(subscription)

            logger.info(f"Subscription updated: {subscription_id}")
            return subscription

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def cancel(
            db: Session,
            subscription_id: UUID,
            cancellation_reason: Optional[str] = None
    ) -> Optional[SubscriptionModel]:
        """
        Cancel a subscription.

        Args:
            db: Database session
            subscription_id: Subscription UUID
            cancellation_reason: Optional reason for cancellation

        Returns:
            SubscriptionModel or None if not found
        """
        try:
            subscription = SubscriptionRepository.get_by_id(db, subscription_id)
            if not subscription:
                return None

            subscription.status = SubscriptionStatusEnum.CANCELED
            subscription.cancellation_date = date.today()
            subscription.cancellation_reason = cancellation_reason

            db.commit()
            db.refresh(subscription)

            logger.info(f"Subscription canceled: {subscription_id}")
            return subscription

        except Exception as e:
            db.rollback()
            logger.error(f"Error canceling subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def delete(db: Session, subscription_id: UUID) -> bool:
        """
        Hard delete a subscription (permanent removal).

        Use with caution - this is permanent deletion.
        Prefer cancel() for soft delete behavior.

        Args:
            db: Database session
            subscription_id: Subscription UUID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            subscription = SubscriptionRepository.get_by_id(db, subscription_id)
            if not subscription:
                return False

            db.delete(subscription)
            db.commit()

            logger.warning(f"Subscription hard deleted: {subscription_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def get_all(
            db: Session,
            limit: int = 100,
            offset: int = 0
    ) -> List[SubscriptionModel]:
        """
        Get all subscriptions with pagination.

        Args:
            db: Database session
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List[SubscriptionModel]: List of subscriptions
        """
        return db.query(SubscriptionModel).order_by(
            desc(SubscriptionModel.created_at)
        ).limit(limit).offset(offset).all()

    @staticmethod
    def count_by_client(db: Session, client_id: UUID) -> int:
        """
        Count total subscriptions for a client.

        Args:
            db: Database session
            client_id: Client UUID

        Returns:
            int: Total count
        """
        return db.query(SubscriptionModel).filter(
            SubscriptionModel.client_id == client_id
        ).count()

    @staticmethod
    def count_by_status(db: Session, status: SubscriptionStatusEnum) -> int:
        """
        Count subscriptions by status.

        Args:
            db: Database session
            status: SubscriptionStatusEnum

        Returns:
            int: Total count
        """
        return db.query(SubscriptionModel).filter(
            SubscriptionModel.status == status
        ).count()

    @staticmethod
    def get_expiring_soon(
            db: Session,
            days_threshold: int = 7
    ) -> List[SubscriptionModel]:
        """
        Get subscriptions expiring within a threshold (for renewal reminders).

        Args:
            db: Database session
            days_threshold: Days from now to check (default: 7)

        Returns:
            List[SubscriptionModel]: List of subscriptions expiring soon
        """
        from datetime import timedelta

        threshold_date = date.today() + timedelta(days=days_threshold)

        return db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE,
                SubscriptionModel.end_date <= threshold_date
            )
        ).order_by(SubscriptionModel.end_date).all()

    @staticmethod
    def get_expired(db: Session) -> List[SubscriptionModel]:
        """
        Get expired subscriptions (status still ACTIVE but end_date passed).

        Useful for batch updating subscriptions to EXPIRED status.

        Args:
            db: Database session

        Returns:
            List[SubscriptionModel]: List of expired subscriptions
        """
        return db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE,
                SubscriptionModel.end_date < date.today()
            )
        ).all()