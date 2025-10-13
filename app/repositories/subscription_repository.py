from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.models import SubscriptionModel, SubscriptionStatusEnum
from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal

class SubscriptionRepository:
    @staticmethod
    def create(db: Session, client_id: UUID, plan_id: UUID, start_date: date,
               end_date: date, original_price: Decimal, discount_amount: Decimal,
               final_price: Decimal, status: SubscriptionStatusEnum = SubscriptionStatusEnum.PENDING_PAYMENT,
               auto_renew: bool = False) -> SubscriptionModel:
        """
        Create a new subscription in the database.
        """
        db_subscription = SubscriptionModel(
            client_id=client_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            original_price=original_price,
            discount_amount=discount_amount,
            final_price=final_price,
            status=status,
            auto_renew=auto_renew
        )
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)
        return db_subscription

    @staticmethod
    def get_by_id(db: Session, subscription_id: UUID) -> Optional[SubscriptionModel]:
        """
        Get subscription by ID.
        """
        return db.query(SubscriptionModel).filter(SubscriptionModel.id == subscription_id).first()

    @staticmethod
    def get_by_client(db: Session, client_id: UUID, limit: int = 100,
                      offset: int = 0) -> List[SubscriptionModel]:
        """
        Get all subscriptions for a specific client.
        """
        return db.query(SubscriptionModel).filter(
            SubscriptionModel.client_id == client_id
        ).order_by(SubscriptionModel.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_by_plan(db: Session, plan_id: UUID, limit: int = 100,
                    offset: int = 0) -> List[SubscriptionModel]:
        """
        Get all subscriptions for a specific plan.
        """
        return db.query(SubscriptionModel).filter(
            SubscriptionModel.plan_id == plan_id
        ).order_by(SubscriptionModel.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_by_status(db: Session, status: SubscriptionStatusEnum, limit: int = 100,
                      offset: int = 0) -> List[SubscriptionModel]:
        """
        Get all subscriptions with a specific status.
        """
        return db.query(SubscriptionModel).filter(
            SubscriptionModel.status == status
        ).order_by(SubscriptionModel.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_active_by_client(db: Session, client_id: UUID) -> List[SubscriptionModel]:
        """
        Get all active subscriptions for a specific client.
        """
        return db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.client_id == client_id,
                SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE
            )
        ).all()

    @staticmethod
    def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[SubscriptionModel]:
        """
        Get all subscriptions.
        """
        return db.query(SubscriptionModel).order_by(
            SubscriptionModel.created_at.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def update(db: Session, subscription_id: UUID, **kwargs) -> Optional[SubscriptionModel]:
        """
        Update subscription by ID.
        """
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.id == subscription_id
        ).first()
        if not subscription:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(subscription, key):
                setattr(subscription, key, value)

        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def cancel(db: Session, subscription_id: UUID, cancellation_reason: Optional[str] = None) -> Optional[SubscriptionModel]:
        """
        Cancel a subscription.
        """
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.id == subscription_id
        ).first()
        if not subscription:
            return None

        subscription.status = SubscriptionStatusEnum.CANCELED
        subscription.cancellation_date = date.today()
        if cancellation_reason:
            subscription.cancellation_reason = cancellation_reason

        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def delete(db: Session, subscription_id: UUID) -> bool:
        """
        Hard delete subscription (use with caution).
        """
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.id == subscription_id
        ).first()
        if not subscription:
            return False

        db.delete(subscription)
        db.commit()
        return True

    @staticmethod
    async def create_async(db: AsyncSession, client_id: UUID, plan_id: UUID,
                          start_date: date, end_date: date, original_price: Decimal,
                          discount_amount: Decimal, final_price: Decimal,
                          status: SubscriptionStatusEnum = SubscriptionStatusEnum.PENDING_PAYMENT,
                          auto_renew: bool = False) -> SubscriptionModel:
        """
        Create a new subscription in the database (async).
        """
        db_subscription = SubscriptionModel(
            client_id=client_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            original_price=original_price,
            discount_amount=discount_amount,
            final_price=final_price,
            status=status,
            auto_renew=auto_renew
        )
        db.add(db_subscription)
        await db.commit()
        await db.refresh(db_subscription)
        return db_subscription

    @staticmethod
    async def get_by_id_async(db: AsyncSession, subscription_id: UUID) -> Optional[SubscriptionModel]:
        """
        Get subscription by ID (async).
        """
        result = await db.execute(select(SubscriptionModel).filter(
            SubscriptionModel.id == subscription_id
        ))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_client_async(db: AsyncSession, client_id: UUID, limit: int = 100,
                                  offset: int = 0) -> List[SubscriptionModel]:
        """
        Get all subscriptions for a specific client (async).
        """
        query = select(SubscriptionModel).filter(
            SubscriptionModel.client_id == client_id
        ).order_by(SubscriptionModel.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_plan_async(db: AsyncSession, plan_id: UUID, limit: int = 100,
                                offset: int = 0) -> List[SubscriptionModel]:
        """
        Get all subscriptions for a specific plan (async).
        """
        query = select(SubscriptionModel).filter(
            SubscriptionModel.plan_id == plan_id
        ).order_by(SubscriptionModel.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_status_async(db: AsyncSession, status: SubscriptionStatusEnum,
                                  limit: int = 100, offset: int = 0) -> List[SubscriptionModel]:
        """
        Get all subscriptions with a specific status (async).
        """
        query = select(SubscriptionModel).filter(
            SubscriptionModel.status == status
        ).order_by(SubscriptionModel.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_active_by_client_async(db: AsyncSession, client_id: UUID) -> List[SubscriptionModel]:
        """
        Get all active subscriptions for a specific client (async).
        """
        query = select(SubscriptionModel).filter(
            and_(
                SubscriptionModel.client_id == client_id,
                SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE
            )
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_all_async(db: AsyncSession, limit: int = 100, offset: int = 0) -> List[SubscriptionModel]:
        """
        Get all subscriptions (async).
        """
        query = select(SubscriptionModel).order_by(
            SubscriptionModel.created_at.desc()
        ).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_async(db: AsyncSession, subscription_id: UUID, **kwargs) -> Optional[SubscriptionModel]:
        """
        Update subscription by ID (async).
        """
        result = await db.execute(select(SubscriptionModel).filter(
            SubscriptionModel.id == subscription_id
        ))
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(subscription, key):
                setattr(subscription, key, value)

        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def cancel_async(db: AsyncSession, subscription_id: UUID,
                          cancellation_reason: Optional[str] = None) -> Optional[SubscriptionModel]:
        """
        Cancel a subscription (async).
        """
        result = await db.execute(select(SubscriptionModel).filter(
            SubscriptionModel.id == subscription_id
        ))
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        subscription.status = SubscriptionStatusEnum.CANCELED
        subscription.cancellation_date = date.today()
        if cancellation_reason:
            subscription.cancellation_reason = cancellation_reason

        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def delete_async(db: AsyncSession, subscription_id: UUID) -> bool:
        """
        Hard delete subscription (async, use with caution).
        """
        result = await db.execute(select(SubscriptionModel).filter(
            SubscriptionModel.id == subscription_id
        ))
        subscription = result.scalar_one_or_none()

        if not subscription:
            return False

        await db.delete(subscription)
        await db.commit()
        return True
