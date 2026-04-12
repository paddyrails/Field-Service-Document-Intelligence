from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.collections import VISITS
from common.models.visit import Visit, VisitStatus


class VisitDAO:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[VISITS]

    async def insert(self, visit: Visit) -> str:
        result = await self.collection.insert_one(visit.to_mongo())
        return str(result.inserted_id)

    async def find_by_id(self, visit_id: str) -> Visit | None:
        doc = await self.collection.find_one({"_id": ObjectId(visit_id)})
        return Visit.from_mongo(doc) if doc else None

    async def find_by_patient(self, patient_id: str) -> list[Visit]:
        cursor = self.collection.find({"patient_id": patient_id}).sort("scheduled_at", 1)
        return [Visit.from_mongo(doc) async for doc in cursor]

    async def update_status(self, visit_id: str, status: VisitStatus) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(visit_id)},
            {"$set": {"status": status.value, "updated_at": datetime.now(timezone.utc)}},
        )
        return result.modified_count == 1

    async def assign_visit(self, visit_id: str, slack_user_id: str) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(visit_id)},
            {"$set": {
                "assigned_to": slack_user_id,
                "status": VisitStatus.SCHEDULED.value,
                "updated_at": datetime.now(timezone.utc),
            }},
        )
        return result.modified_count == 1
