from sqlalchemy.orm import Session
from uuid import UUID
from app.schemas.subscription import Subscription, SubscriptionCreate, SubscriptionRenew, SubscriptionCancel
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.plan_repository import PlanRepository
from app.db.models import SubscriptionStatusEnum
from app.utils.subscription.calculator import SubscriptionCalculator
from typing import List, Optional


class SubscriptionService:
    """Business logic for subscriptions"""

    @staticmethod
    def create_subscription(db: Session, subscription_data: SubscriptionCreate) -> Subscription:
        """Create a new subscription"""
        plan = PlanRepository.get_by_id(db, subscription_data.plan_id)
        end_date = SubscriptionCalculator.calculate_end_date(subscription_data.start_date, plan)

        subscription_model = SubscriptionRepository.create(
            db=db,
            client_id=subscription_data.client_id,
            plan_id=subscription_data.plan_id,
            start_date=subscription_data.start_date,
            end_date=end_date,
            status=SubscriptionStatusEnum.PENDING_PAYMENT
        )

        return Subscription.from_orm(subscription_model)

    @staticmethod
    def get_active_subscription_by_client(db: Session, client_id: UUID) -> Optional[Subscription]:
        """Get the active subscription for a client (only one can exist)"""
        subscriptions = SubscriptionRepository.get_active_by_client(db, client_id)
        if subscriptions:
            return Subscription.from_orm(subscriptions[0])
        return None

    @staticmethod
    def get_subscriptions_by_client(
            db: Session,
            client_id: UUID,
            limit: int = 100,
            offset: int = 0
    ) -> List[Subscription]:
        """Get all subscriptions for a client"""
        subscription_models = SubscriptionRepository.get_by_client(db, client_id, limit, offset)
        return [Subscription.from_orm(sub) for sub in subscription_models]

    @staticmethod
    def renew_subscription(
            db: Session,
            renewal_data: SubscriptionRenew
    ) -> Subscription:
        """
        Renew a subscription.

        Logic:
        - Takes the current subscription's end_date and adds 1 day as start_date
        - Uses provided plan_id, or same plan if not specified
        - New subscription always starts as PENDING_PAYMENT
        """
        from datetime import timedelta

        old_sub = SubscriptionRepository.get_by_id(db, renewal_data.subscription_id)

        # Use provided plan or keep the same plan
        plan_id = renewal_data.plan_id or old_sub.plan_id
        plan = PlanRepository.get_by_id(db, plan_id)

        # Renewal always starts the day after current subscription ends
        renewal_start = old_sub.end_date + timedelta(days=1)
        end_date = SubscriptionCalculator.calculate_end_date(renewal_start, plan)

        subscription_model = SubscriptionRepository.create(
            db=db,
            client_id=renewal_data.client_id,
            plan_id=plan_id,
            start_date=renewal_start,
            end_date=end_date,
            status=SubscriptionStatusEnum.PENDING_PAYMENT
        )

        return Subscription.from_orm(subscription_model)

    @staticmethod
    def cancel_subscription(
            db: Session,
            cancel_data: SubscriptionCancel
    ) -> Subscription:
        """Cancel a subscription"""
        subscription_model = SubscriptionRepository.cancel(
            db=db,
            subscription_id=cancel_data.subscription_id,
            cancellation_reason=cancel_data.cancellation_reason
        )

        return Subscription.from_orm(subscription_model)
