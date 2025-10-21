# app/utils/payment/schema_builder.py

from app.schemas.payment import PaymentCreateInput, PaymentCreate
from uuid import UUID


class PaymentSchemaBuilder:
    """Schema builders for payments"""

    @staticmethod
    def build_create(subscription_id: UUID, input_data: PaymentCreateInput) -> PaymentCreate:
        """
        Build PaymentCreate from input.

        Injects subscription_id from the route parameter.

        Args:
            subscription_id: Subscription UUID from route
            input_data: PaymentCreateInput from request body

        Returns:
            PaymentCreate: Internal schema ready for service layer
        """
        return PaymentCreate(
            subscription_id=subscription_id,
            amount=input_data.amount,
            payment_method=input_data.payment_method
        )