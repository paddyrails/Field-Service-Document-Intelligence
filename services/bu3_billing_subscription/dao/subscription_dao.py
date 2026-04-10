from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.collections import SUBSCRIPTIONS
from common.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus


class SubscriptionDAO:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[SUBSCRIPTIONS]

    async def insert(self, subscription: Subscription) -> str:
        result = await self.collection.insert_one(subscription.to_mongo())
        return str(result.inserted_id)

    async def find_by_customer(self, customer_id: str) -> Subscription | None:
        doc = await self.collection.find_one({"customer_id": customer_id})
        return Subscription.from_mongo(doc) if doc else None

    async def update(
        self,
        customer_id: str,
        plan: SubscriptionPlan,
        status: SubscriptionStatus,
        monthly_fee: float,
    ) -> bool:
        result = await self.collection.update_one(
            {"customer_id": customer_id},
            {
                "$set": {
                    "plan": plan.value,
                    "status": status.value,
                    "monthly_fee": monthly_fee,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.modified_count == 1
