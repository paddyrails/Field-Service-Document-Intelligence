from common.exceptions.handlers import SubscriptionNotFoundError
from common.models.subscription import Subscription
from common.schemas.request import SubscriptionCreateRequest, SubscriptionUpdateRequest
from common.schemas.response import SubscriptionResponse
from dao.subscription_dao import SubscriptionDAO


class SubscriptionService:
    def __init__(self, dao: SubscriptionDAO) -> None:
        self.dao = dao

    async def create_subscription(
        self, request: SubscriptionCreateRequest
    ) -> SubscriptionResponse:
        subscription = Subscription(
            customer_id=request.customer_id,
            plan=request.plan,
            start_date=request.start_date,
            renewal_date=request.renewal_date,
            monthly_fee=request.monthly_fee,
        )
        sub_id = await self.dao.insert(subscription)
        created = await self.dao.find_by_customer(request.customer_id)
        return self._to_response(created)  # type: ignore[arg-type]

    async def get_subscription(self, customer_id: str) -> SubscriptionResponse:
        subscription = await self.dao.find_by_customer(customer_id)
        if subscription is None:
            raise SubscriptionNotFoundError(customer_id)
        return self._to_response(subscription)

    async def update_subscription(
        self, customer_id: str, request: SubscriptionUpdateRequest
    ) -> SubscriptionResponse:
        subscription = await self.dao.find_by_customer(customer_id)
        if subscription is None:
            raise SubscriptionNotFoundError(customer_id)
        await self.dao.update(customer_id, request.plan, request.status, request.monthly_fee)
        updated = await self.dao.find_by_customer(customer_id)
        return self._to_response(updated)  # type: ignore[arg-type]

    def _to_response(self, subscription: Subscription) -> SubscriptionResponse:
        return SubscriptionResponse(
            id=str(subscription.id),
            customer_id=subscription.customer_id,
            plan=subscription.plan,
            status=subscription.status,
            start_date=subscription.start_date,
            renewal_date=subscription.renewal_date,
            monthly_fee=subscription.monthly_fee,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )
