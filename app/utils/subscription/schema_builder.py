from app.schemas.subscription import (
    SubscriptionCreateInput,
    SubscriptionCreate,
    SubscriptionRenewInput,
    SubscriptionRenew,
    SubscriptionCancelInput,
    SubscriptionCancel
)
from uuid import UUID


class SubscriptionSchemaBuilder:
    """Schema builders for subscriptions"""

    @staticmethod
    def build_create(client_id: UUID, input_data: SubscriptionCreateInput) -> SubscriptionCreate:
        """Build SubscriptionCreate by injecting client_id from route"""
        return SubscriptionCreate(
            client_id=client_id,
            plan_id=input_data.plan_id,
            start_date=input_data.start_date
        )

    @staticmethod
    def build_renew(
        client_id: UUID,
        subscription_id: UUID,
        input_data: SubscriptionRenewInput
    ) -> SubscriptionRenew:
        """
        Build SubscriptionRenew by injecting client_id and subscription_id.
        plan_id is optional - if not provided, same plan will be used.
        """
        return SubscriptionRenew(
            client_id=client_id,
            subscription_id=subscription_id,
            plan_id=input_data.plan_id
        )

    @staticmethod
    def build_cancel(
        subscription_id: UUID,
        input_data: SubscriptionCancelInput
    ) -> SubscriptionCancel:
        """Build SubscriptionCancel"""
        return SubscriptionCancel(
            subscription_id=subscription_id,
            cancellation_reason=input_data.cancellation_reason
        )
