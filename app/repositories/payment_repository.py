from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.models import PaymentModel, PaymentStatusEnum, PaymentMethodEnum
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class PaymentRepository:
    @staticmethod
    def create(db: Session, subscription_id: UUID, amount: Decimal, currency: str,
               payment_method: PaymentMethodEnum, status: PaymentStatusEnum = PaymentStatusEnum.PENDING,
               payment_date: Optional[datetime] = None) -> PaymentModel:
        """
        Create a new payment in the database.
        """
        db_payment = PaymentModel(
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            status=status,
            payment_date=payment_date if payment_date else datetime.now()
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment

    @staticmethod
    def get_by_id(db: Session, payment_id: UUID) -> Optional[PaymentModel]:
        """
        Get payment by ID.
        """
        return db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()

    @staticmethod
    def get_by_subscription(db: Session, subscription_id: UUID, limit: int = 100,
                           offset: int = 0) -> List[PaymentModel]:
        """
        Get all payments for a specific subscription.
        """
        return db.query(PaymentModel).filter(
            PaymentModel.subscription_id == subscription_id
        ).order_by(PaymentModel.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_by_status(db: Session, status: PaymentStatusEnum, limit: int = 100,
                      offset: int = 0) -> List[PaymentModel]:
        """
        Get all payments with a specific status.
        """
        return db.query(PaymentModel).filter(
            PaymentModel.status == status
        ).order_by(PaymentModel.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_by_method(db: Session, payment_method: PaymentMethodEnum, limit: int = 100,
                      offset: int = 0) -> List[PaymentModel]:
        """
        Get all payments with a specific payment method.
        """
        return db.query(PaymentModel).filter(
            PaymentModel.payment_method == payment_method
        ).order_by(PaymentModel.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[PaymentModel]:
        """
        Get all payments.
        """
        return db.query(PaymentModel).order_by(
            PaymentModel.created_at.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def update(db: Session, payment_id: UUID, **kwargs) -> Optional[PaymentModel]:
        """
        Update payment by ID.
        """
        payment = db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        if not payment:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(payment, key):
                setattr(payment, key, value)

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def mark_as_completed(db: Session, payment_id: UUID) -> Optional[PaymentModel]:
        """
        Mark a payment as completed.
        """
        payment = db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        if not payment:
            return None

        payment.status = PaymentStatusEnum.COMPLETED
        payment.payment_date = datetime.now()

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def mark_as_failed(db: Session, payment_id: UUID) -> Optional[PaymentModel]:
        """
        Mark a payment as failed.
        """
        payment = db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        if not payment:
            return None

        payment.status = PaymentStatusEnum.FAILED

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def delete(db: Session, payment_id: UUID) -> bool:
        """
        Hard delete payment (use with caution).
        """
        payment = db.query(PaymentModel).filter(PaymentModel.id == payment_id).first()
        if not payment:
            return False

        db.delete(payment)
        db.commit()
        return True

    @staticmethod
    async def create_async(db: AsyncSession, subscription_id: UUID, amount: Decimal,
                          currency: str, payment_method: PaymentMethodEnum,
                          status: PaymentStatusEnum = PaymentStatusEnum.PENDING,
                          payment_date: Optional[datetime] = None) -> PaymentModel:
        """
        Create a new payment in the database (async).
        """
        db_payment = PaymentModel(
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            status=status,
            payment_date=payment_date if payment_date else datetime.now()
        )
        db.add(db_payment)
        await db.commit()
        await db.refresh(db_payment)
        return db_payment

    @staticmethod
    async def get_by_id_async(db: AsyncSession, payment_id: UUID) -> Optional[PaymentModel]:
        """
        Get payment by ID (async).
        """
        result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_subscription_async(db: AsyncSession, subscription_id: UUID,
                                       limit: int = 100, offset: int = 0) -> List[PaymentModel]:
        """
        Get all payments for a specific subscription (async).
        """
        query = select(PaymentModel).filter(
            PaymentModel.subscription_id == subscription_id
        ).order_by(PaymentModel.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_status_async(db: AsyncSession, status: PaymentStatusEnum,
                                  limit: int = 100, offset: int = 0) -> List[PaymentModel]:
        """
        Get all payments with a specific status (async).
        """
        query = select(PaymentModel).filter(
            PaymentModel.status == status
        ).order_by(PaymentModel.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_method_async(db: AsyncSession, payment_method: PaymentMethodEnum,
                                  limit: int = 100, offset: int = 0) -> List[PaymentModel]:
        """
        Get all payments with a specific payment method (async).
        """
        query = select(PaymentModel).filter(
            PaymentModel.payment_method == payment_method
        ).order_by(PaymentModel.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_all_async(db: AsyncSession, limit: int = 100, offset: int = 0) -> List[PaymentModel]:
        """
        Get all payments (async).
        """
        query = select(PaymentModel).order_by(
            PaymentModel.created_at.desc()
        ).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_async(db: AsyncSession, payment_id: UUID, **kwargs) -> Optional[PaymentModel]:
        """
        Update payment by ID (async).
        """
        result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(payment, key):
                setattr(payment, key, value)

        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def mark_as_completed_async(db: AsyncSession, payment_id: UUID) -> Optional[PaymentModel]:
        """
        Mark a payment as completed (async).
        """
        result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            return None

        payment.status = PaymentStatusEnum.COMPLETED
        payment.payment_date = datetime.now()

        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def mark_as_failed_async(db: AsyncSession, payment_id: UUID) -> Optional[PaymentModel]:
        """
        Mark a payment as failed (async).
        """
        result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            return None

        payment.status = PaymentStatusEnum.FAILED

        await db.commit()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def delete_async(db: AsyncSession, payment_id: UUID) -> bool:
        """
        Hard delete payment (async, use with caution).
        """
        result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            return False

        await db.delete(payment)
        await db.commit()
        return True
