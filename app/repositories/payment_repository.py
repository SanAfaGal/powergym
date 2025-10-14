from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import PaymentModel
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

class PaymentRepository:
    @staticmethod
    def create(db: Session, subscription_id: UUID, amount: Decimal,
               payment_method: str, meta_info: dict = None) -> PaymentModel:
        """
        Create a new payment in the database.
        """
        db_payment = PaymentModel(
            subscription_id=subscription_id,
            amount=amount,
            payment_method=payment_method,
            meta_info=meta_info or {}
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
        ).order_by(PaymentModel.payment_date.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[PaymentModel]:
        """
        Get all payments.
        """
        return db.query(PaymentModel).order_by(
            PaymentModel.payment_date.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_total_paid_for_subscription(db: Session, subscription_id: UUID) -> Decimal:
        """
        Calculate total amount paid for a subscription.
        """
        from sqlalchemy import func
        result = db.query(func.sum(PaymentModel.amount)).filter(
            PaymentModel.subscription_id == subscription_id
        ).scalar()
        return result or Decimal('0.00')

    @staticmethod
    def delete(db: Session, payment_id: UUID) -> bool:
        """
        Hard delete payment (use with caution).
        """
        payment = db.query(PaymentModel).filter(
            PaymentModel.id == payment_id
        ).first()
        if not payment:
            return False

        db.delete(payment)
        db.commit()
        return True
