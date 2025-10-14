from sqlalchemy.orm import Session
from app.models.subscription import Subscription, SubscriptionCreate, SubscriptionUpdate, SubscriptionStatus
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.plan_repository import PlanRepository
from app.db.models import SubscriptionStatusEnum
from uuid import UUID
from typing import List, Optional
from datetime import date


class SubscriptionService:
    @staticmethod
    def create_subscription(db: Session, subscription_data: SubscriptionCreate) -> Subscription:
        """
        Create a new subscription after validating client and plan existence.
        """
        client = ClientRepository.get_by_id(db, subscription_data.client_id)
        if not client:
            raise ValueError("Client not found")

        plan = PlanRepository.get_by_id(db, subscription_data.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        if not plan.is_active:
            raise ValueError("Plan is not active")

        status_enum = SubscriptionStatusEnum[subscription_data.status.value.upper()]

        subscription_model = SubscriptionRepository.create(
            db=db,
            client_id=subscription_data.client_id,
            plan_id=subscription_data.plan_id,
            start_date=subscription_data.start_date,
            end_date=subscription_data.end_date,
            original_price=subscription_data.original_price,
            discount_amount=subscription_data.discount_amount,
            final_price=subscription_data.final_price,
            status=status_enum,
            auto_renew=subscription_data.auto_renew
        )

        return Subscription(
            id=subscription_model.id,
            client_id=subscription_model.client_id,
            plan_id=subscription_model.plan_id,
            start_date=subscription_model.start_date,
            end_date=subscription_model.end_date,
            original_price=subscription_model.original_price,
            discount_amount=subscription_model.discount_amount,
            final_price=subscription_model.final_price,
            status=SubscriptionStatus(subscription_model.status.value),
            auto_renew=subscription_model.auto_renew,
            cancellation_date=subscription_model.cancellation_date,
            cancellation_reason=subscription_model.cancellation_reason,
            created_at=subscription_model.created_at,
            updated_at=subscription_model.updated_at,
            meta_info=subscription_model.meta_info
        )

    @staticmethod
    def get_subscription_by_id(db: Session, subscription_id: UUID) -> Optional[Subscription]:
        """
        Get a subscription by its ID.
        """
        subscription_model = SubscriptionRepository.get_by_id(db, subscription_id)

        if subscription_model:
            return Subscription(
                id=subscription_model.id,
                client_id=subscription_model.client_id,
                plan_id=subscription_model.plan_id,
                start_date=subscription_model.start_date,
                end_date=subscription_model.end_date,
                original_price=subscription_model.original_price,
                discount_amount=subscription_model.discount_amount,
                final_price=subscription_model.final_price,
                status=SubscriptionStatus(subscription_model.status.value),
                auto_renew=subscription_model.auto_renew,
                cancellation_date=subscription_model.cancellation_date,
                cancellation_reason=subscription_model.cancellation_reason,
                created_at=subscription_model.created_at,
                updated_at=subscription_model.updated_at,
                meta_info=subscription_model.meta_info
            )
        return None

    @staticmethod
    def get_subscriptions_by_client(
        db: Session,
        client_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Subscription]:
        """
        Get all subscriptions for a specific client.
        """
        subscription_models = SubscriptionRepository.get_by_client(db, client_id, limit, offset)

        return [
            Subscription(
                id=sub.id,
                client_id=sub.client_id,
                plan_id=sub.plan_id,
                start_date=sub.start_date,
                end_date=sub.end_date,
                original_price=sub.original_price,
                discount_amount=sub.discount_amount,
                final_price=sub.final_price,
                status=SubscriptionStatus(sub.status.value),
                auto_renew=sub.auto_renew,
                cancellation_date=sub.cancellation_date,
                cancellation_reason=sub.cancellation_reason,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
                meta_info=sub.meta_info
            )
            for sub in subscription_models
        ]

    @staticmethod
    def get_subscriptions_by_plan(
        db: Session,
        plan_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Subscription]:
        """
        Get all subscriptions for a specific plan.
        """
        subscription_models = SubscriptionRepository.get_by_plan(db, plan_id, limit, offset)

        return [
            Subscription(
                id=sub.id,
                client_id=sub.client_id,
                plan_id=sub.plan_id,
                start_date=sub.start_date,
                end_date=sub.end_date,
                original_price=sub.original_price,
                discount_amount=sub.discount_amount,
                final_price=sub.final_price,
                status=SubscriptionStatus(sub.status.value),
                auto_renew=sub.auto_renew,
                cancellation_date=sub.cancellation_date,
                cancellation_reason=sub.cancellation_reason,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
                meta_info=sub.meta_info
            )
            for sub in subscription_models
        ]

    @staticmethod
    def get_subscriptions_by_status(
        db: Session,
        status: SubscriptionStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[Subscription]:
        """
        Get all subscriptions with a specific status.
        """
        status_enum = SubscriptionStatusEnum[status.value.upper()]
        subscription_models = SubscriptionRepository.get_by_status(db, status_enum, limit, offset)

        return [
            Subscription(
                id=sub.id,
                client_id=sub.client_id,
                plan_id=sub.plan_id,
                start_date=sub.start_date,
                end_date=sub.end_date,
                original_price=sub.original_price,
                discount_amount=sub.discount_amount,
                final_price=sub.final_price,
                status=SubscriptionStatus(sub.status.value),
                auto_renew=sub.auto_renew,
                cancellation_date=sub.cancellation_date,
                cancellation_reason=sub.cancellation_reason,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
                meta_info=sub.meta_info
            )
            for sub in subscription_models
        ]

    @staticmethod
    def get_active_subscriptions_by_client(db: Session, client_id: UUID) -> List[Subscription]:
        """
        Get all active subscriptions for a specific client.
        """
        subscription_models = SubscriptionRepository.get_active_by_client(db, client_id)

        return [
            Subscription(
                id=sub.id,
                client_id=sub.client_id,
                plan_id=sub.plan_id,
                start_date=sub.start_date,
                end_date=sub.end_date,
                original_price=sub.original_price,
                discount_amount=sub.discount_amount,
                final_price=sub.final_price,
                status=SubscriptionStatus(sub.status.value),
                auto_renew=sub.auto_renew,
                cancellation_date=sub.cancellation_date,
                cancellation_reason=sub.cancellation_reason,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
                meta_info=sub.meta_info
            )
            for sub in subscription_models
        ]

    @staticmethod
    def list_all_subscriptions(
        db: Session,
        limit: int = 100,
        offset: int = 0
    ) -> List[Subscription]:
        """
        Get all subscriptions with pagination.
        """
        subscription_models = SubscriptionRepository.get_all(db, limit, offset)

        return [
            Subscription(
                id=sub.id,
                client_id=sub.client_id,
                plan_id=sub.plan_id,
                start_date=sub.start_date,
                end_date=sub.end_date,
                original_price=sub.original_price,
                discount_amount=sub.discount_amount,
                final_price=sub.final_price,
                status=SubscriptionStatus(sub.status.value),
                auto_renew=sub.auto_renew,
                cancellation_date=sub.cancellation_date,
                cancellation_reason=sub.cancellation_reason,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
                meta_info=sub.meta_info
            )
            for sub in subscription_models
        ]

    @staticmethod
    def update_subscription(
        db: Session,
        subscription_id: UUID,
        subscription_update: SubscriptionUpdate
    ) -> Optional[Subscription]:
        """
        Update a subscription with the provided data.
        """
        update_dict = {}

        if subscription_update.start_date is not None:
            update_dict["start_date"] = subscription_update.start_date
        if subscription_update.end_date is not None:
            update_dict["end_date"] = subscription_update.end_date
        if subscription_update.original_price is not None:
            update_dict["original_price"] = subscription_update.original_price
        if subscription_update.discount_amount is not None:
            update_dict["discount_amount"] = subscription_update.discount_amount
        if subscription_update.final_price is not None:
            update_dict["final_price"] = subscription_update.final_price
        if subscription_update.status is not None:
            update_dict["status"] = SubscriptionStatusEnum[subscription_update.status.value.upper()]
        if subscription_update.auto_renew is not None:
            update_dict["auto_renew"] = subscription_update.auto_renew
        if subscription_update.cancellation_date is not None:
            update_dict["cancellation_date"] = subscription_update.cancellation_date
        if subscription_update.cancellation_reason is not None:
            update_dict["cancellation_reason"] = subscription_update.cancellation_reason

        if not update_dict:
            return SubscriptionService.get_subscription_by_id(db, subscription_id)

        subscription_model = SubscriptionRepository.update(db, subscription_id, **update_dict)

        if subscription_model:
            return Subscription(
                id=subscription_model.id,
                client_id=subscription_model.client_id,
                plan_id=subscription_model.plan_id,
                start_date=subscription_model.start_date,
                end_date=subscription_model.end_date,
                original_price=subscription_model.original_price,
                discount_amount=subscription_model.discount_amount,
                final_price=subscription_model.final_price,
                status=SubscriptionStatus(subscription_model.status.value),
                auto_renew=subscription_model.auto_renew,
                cancellation_date=subscription_model.cancellation_date,
                cancellation_reason=subscription_model.cancellation_reason,
                created_at=subscription_model.created_at,
                updated_at=subscription_model.updated_at,
                meta_info=subscription_model.meta_info
            )
        return None

    @staticmethod
    def cancel_subscription(
        db: Session,
        subscription_id: UUID,
        cancellation_reason: Optional[str] = None
    ) -> Optional[Subscription]:
        """
        Cancel a subscription.
        """
        subscription_model = SubscriptionRepository.cancel(db, subscription_id, cancellation_reason)

        if subscription_model:
            return Subscription(
                id=subscription_model.id,
                client_id=subscription_model.client_id,
                plan_id=subscription_model.plan_id,
                start_date=subscription_model.start_date,
                end_date=subscription_model.end_date,
                original_price=subscription_model.original_price,
                discount_amount=subscription_model.discount_amount,
                final_price=subscription_model.final_price,
                status=SubscriptionStatus(subscription_model.status.value),
                auto_renew=subscription_model.auto_renew,
                cancellation_date=subscription_model.cancellation_date,
                cancellation_reason=subscription_model.cancellation_reason,
                created_at=subscription_model.created_at,
                updated_at=subscription_model.updated_at,
                meta_info=subscription_model.meta_info
            )
        return None

    @staticmethod
    def delete_subscription(db: Session, subscription_id: UUID) -> bool:
        """
        Hard delete a subscription from the database.
        """
        return SubscriptionRepository.delete(db, subscription_id)

    @staticmethod
    def activate_subscription(db: Session, subscription_id: UUID) -> Optional[Subscription]:
        """
        Activate a subscription by changing its status to ACTIVE.
        """
        subscription = SubscriptionRepository.get_by_id(db, subscription_id)
        if not subscription:
            return None

        if subscription.status == SubscriptionStatusEnum.CANCELED:
            raise ValueError("Cannot activate a canceled subscription")

        update_dict = {"status": SubscriptionStatusEnum.ACTIVE}
        subscription_model = SubscriptionRepository.update(db, subscription_id, **update_dict)

        if subscription_model:
            return Subscription(
                id=subscription_model.id,
                client_id=subscription_model.client_id,
                plan_id=subscription_model.plan_id,
                start_date=subscription_model.start_date,
                end_date=subscription_model.end_date,
                original_price=subscription_model.original_price,
                discount_amount=subscription_model.discount_amount,
                final_price=subscription_model.final_price,
                status=SubscriptionStatus(subscription_model.status.value),
                auto_renew=subscription_model.auto_renew,
                cancellation_date=subscription_model.cancellation_date,
                cancellation_reason=subscription_model.cancellation_reason,
                created_at=subscription_model.created_at,
                updated_at=subscription_model.updated_at,
                meta_info=subscription_model.meta_info
            )
        return None
