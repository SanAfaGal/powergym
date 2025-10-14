from sqlalchemy.orm import Session
from app.models.payment import Payment, PaymentCreate
from app.repositories.payment_repository import PaymentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.plan_repository import PlanRepository
from app.db.models import SubscriptionStatusEnum, PaymentMethodEnum
from uuid import UUID
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class PaymentService:
    @staticmethod
    def _calculate_subscription_duration(plan) -> timedelta:
        """
        Calculate the duration of a subscription based on plan.
        """
        duration_unit = plan.duration_unit.value
        duration_count = plan.duration_count

        if duration_unit == "day":
            return timedelta(days=duration_count)
        elif duration_unit == "week":
            return timedelta(weeks=duration_count)
        elif duration_unit == "month":
            return relativedelta(months=duration_count)
        elif duration_unit == "year":
            return relativedelta(years=duration_count)
        else:
            raise ValueError(f"Invalid duration unit: {duration_unit}")

    @staticmethod
    def _get_pending_balance(db: Session, subscription_id: UUID) -> Decimal:
        """
        Calculate the pending balance for a subscription.
        Returns: pending amount (positive if underpaid, negative if overpaid)
        """
        subscription = SubscriptionRepository.get_by_id(db, subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")

        plan = PlanRepository.get_by_id(db, subscription.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        total_paid = PaymentRepository.get_total_paid_for_subscription(db, subscription_id)
        pending = plan.price - total_paid

        return pending

    @staticmethod
    def _validate_client_active_subscriptions(db: Session, client_id: UUID,
                                              exclude_subscription_id: Optional[UUID] = None) -> None:
        """
        Validate that a client doesn't have multiple active subscriptions.
        """
        active_subs = SubscriptionRepository.get_active_by_client(db, client_id)

        if exclude_subscription_id:
            active_subs = [sub for sub in active_subs if sub.id != exclude_subscription_id]

        if len(active_subs) > 1:
            raise ValueError("Client has multiple active subscriptions. This should not happen.")

    @staticmethod
    def process_payment(db: Session, payment_data: PaymentCreate) -> Dict[str, Any]:
        """
        Process a payment with full business logic:
        - Validates payment amount doesn't exceed pending balance
        - Handles partial payments
        - Handles advance payments for future periods
        - Updates subscription status accordingly
        - Ensures only one active subscription per client
        """
        subscription = SubscriptionRepository.get_by_id(db, payment_data.subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")

        plan = PlanRepository.get_by_id(db, subscription.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        if subscription.status == SubscriptionStatusEnum.CANCELED:
            raise ValueError("Cannot process payment for a canceled subscription")

        total_paid = PaymentRepository.get_total_paid_for_subscription(db, payment_data.subscription_id)
        pending_balance = plan.price - total_paid

        if payment_data.amount > pending_balance and pending_balance > 0:
            raise ValueError(
                f"Payment amount ({payment_data.amount}) exceeds pending balance ({pending_balance}). "
                "Please provide exact or lower amount for partial payment."
            )

        payment_method_enum = PaymentMethodEnum[payment_data.payment_method.value.upper()]

        meta_info = {
            "pending_balance_before": float(pending_balance),
            "total_paid_before": float(total_paid)
        }

        payment_model = PaymentRepository.create(
            db=db,
            subscription_id=payment_data.subscription_id,
            amount=payment_data.amount,
            payment_method=payment_method_enum,
            meta_info=meta_info
        )

        new_total_paid = total_paid + payment_data.amount
        new_pending_balance = plan.price - new_total_paid

        result = {
            "payment": Payment(
                id=payment_model.id,
                subscription_id=payment_model.subscription_id,
                amount=payment_model.amount,
                payment_method=payment_data.payment_method,
                payment_date=payment_model.payment_date,
                meta_info=payment_model.meta_info
            ),
            "total_paid": new_total_paid,
            "pending_balance": new_pending_balance,
            "subscription_status": subscription.status.value,
            "message": ""
        }

        if new_pending_balance <= 0:
            if subscription.status == SubscriptionStatusEnum.PENDING_PAYMENT:
                SubscriptionRepository.update(
                    db, payment_data.subscription_id,
                    status=SubscriptionStatusEnum.ACTIVE
                )
                result["subscription_status"] = "active"
                result["message"] = "Subscription activated. Full payment received."

                PaymentService._validate_client_active_subscriptions(
                    db, subscription.client_id, payment_data.subscription_id
                )

            if new_pending_balance < 0:
                advance_amount = abs(new_pending_balance)
                result["advance_amount"] = advance_amount
                result["message"] = f"Payment processed with advance of {advance_amount}. " \
                                  f"This will be applied to the next period."
        else:
            result["message"] = f"Partial payment received. Pending balance: {new_pending_balance}"

            if subscription.status == SubscriptionStatusEnum.PENDING_PAYMENT:
                result["message"] += " Subscription remains pending until full payment."

        return result

    @staticmethod
    def process_renewal_payment(db: Session, current_subscription_id: UUID,
                               payment_amount: Decimal, payment_method: str) -> Dict[str, Any]:
        """
        Process renewal payment for an active subscription.
        If the current subscription is still active, create a new pending subscription
        and apply the payment to it.
        """
        current_sub = SubscriptionRepository.get_by_id(db, current_subscription_id)
        if not current_sub:
            raise ValueError("Subscription not found")

        if current_sub.status == SubscriptionStatusEnum.CANCELED:
            raise ValueError("Cannot renew a canceled subscription")

        plan = PlanRepository.get_by_id(db, current_sub.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        if not plan.is_active:
            raise ValueError("Cannot renew with an inactive plan")

        if payment_amount > plan.price:
            raise ValueError(
                f"Payment amount ({payment_amount}) exceeds plan price ({plan.price}). "
                "Please provide exact or lower amount."
            )

        grace_period_days = 7
        is_within_grace_period = (
            current_sub.status == SubscriptionStatusEnum.ACTIVE and
            (current_sub.end_date - date.today()).days <= grace_period_days
        )

        if current_sub.status == SubscriptionStatusEnum.ACTIVE and not is_within_grace_period:
            total_paid = PaymentRepository.get_total_paid_for_subscription(db, current_subscription_id)
            advance_credit = total_paid - plan.price

            if advance_credit > 0:
                new_start_date = current_sub.end_date
                duration = PaymentService._calculate_subscription_duration(plan)

                if isinstance(duration, timedelta):
                    new_end_date = new_start_date + duration
                else:
                    new_end_date = new_start_date + duration

                new_sub = SubscriptionRepository.create(
                    db=db,
                    client_id=current_sub.client_id,
                    plan_id=current_sub.plan_id,
                    start_date=new_start_date,
                    end_date=new_end_date,
                    status=SubscriptionStatusEnum.PENDING_PAYMENT,
                    meta_info={"created_from_advance": True, "advance_credit": float(advance_credit)}
                )

                payment_data = PaymentCreate(
                    subscription_id=new_sub.id,
                    amount=payment_amount,
                    payment_method=PaymentMethodEnum[payment_method.upper()]
                )

                return PaymentService.process_payment(db, payment_data)
            else:
                raise ValueError(
                    "Current subscription is still active and not within grace period. "
                    "No advance credit available to create a new subscription."
                )

        if is_within_grace_period or current_sub.status == SubscriptionStatusEnum.EXPIRED:
            new_start_date = max(current_sub.end_date, date.today())
            duration = PaymentService._calculate_subscription_duration(plan)

            if isinstance(duration, timedelta):
                new_end_date = new_start_date + duration
            else:
                new_end_date = new_start_date + duration

            new_sub = SubscriptionRepository.create(
                db=db,
                client_id=current_sub.client_id,
                plan_id=current_sub.plan_id,
                start_date=new_start_date,
                end_date=new_end_date,
                status=SubscriptionStatusEnum.PENDING_PAYMENT,
                meta_info={"renewed_from": str(current_subscription_id)}
            )

            payment_data = PaymentCreate(
                subscription_id=new_sub.id,
                amount=payment_amount,
                payment_method=PaymentMethodEnum[payment_method.upper()]
            )

            result = PaymentService.process_payment(db, payment_data)
            result["new_subscription_id"] = new_sub.id
            result["message"] = f"Renewal payment processed. {result['message']}"

            return result

        raise ValueError("Unable to process renewal payment. Invalid subscription state.")

    @staticmethod
    def get_payment_by_id(db: Session, payment_id: UUID) -> Optional[Payment]:
        """
        Get a payment by its ID.
        """
        payment_model = PaymentRepository.get_by_id(db, payment_id)

        if payment_model:
            return Payment(
                id=payment_model.id,
                subscription_id=payment_model.subscription_id,
                amount=payment_model.amount,
                payment_method=payment_model.payment_method.value,
                payment_date=payment_model.payment_date,
                meta_info=payment_model.meta_info
            )
        return None

    @staticmethod
    def get_payments_by_subscription(db: Session, subscription_id: UUID,
                                     limit: int = 100, offset: int = 0) -> List[Payment]:
        """
        Get all payments for a specific subscription.
        """
        payment_models = PaymentRepository.get_by_subscription(db, subscription_id, limit, offset)

        return [
            Payment(
                id=payment.id,
                subscription_id=payment.subscription_id,
                amount=payment.amount,
                payment_method=payment.payment_method.value,
                payment_date=payment.payment_date,
                meta_info=payment.meta_info
            )
            for payment in payment_models
        ]

    @staticmethod
    def list_all_payments(db: Session, limit: int = 100, offset: int = 0) -> List[Payment]:
        """
        Get all payments with pagination.
        """
        payment_models = PaymentRepository.get_all(db, limit, offset)

        return [
            Payment(
                id=payment.id,
                subscription_id=payment.subscription_id,
                amount=payment.amount,
                payment_method=payment.payment_method.value,
                payment_date=payment.payment_date,
                meta_info=payment.meta_info
            )
            for payment in payment_models
        ]

    @staticmethod
    def get_subscription_payment_summary(db: Session, subscription_id: UUID) -> Dict[str, Any]:
        """
        Get payment summary for a subscription including balance and status.
        """
        subscription = SubscriptionRepository.get_by_id(db, subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")

        plan = PlanRepository.get_by_id(db, subscription.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        total_paid = PaymentRepository.get_total_paid_for_subscription(db, subscription_id)
        pending_balance = plan.price - total_paid
        advance_amount = abs(pending_balance) if pending_balance < 0 else Decimal('0.00')

        payments = PaymentRepository.get_by_subscription(db, subscription_id)

        return {
            "subscription_id": subscription_id,
            "plan_price": plan.price,
            "total_paid": total_paid,
            "pending_balance": max(pending_balance, Decimal('0.00')),
            "advance_amount": advance_amount,
            "payment_count": len(payments),
            "subscription_status": subscription.status.value,
            "is_fully_paid": pending_balance <= 0
        }
