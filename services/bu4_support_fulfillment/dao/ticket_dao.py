from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.collections import TICKETS
from common.models.ticket import Ticket, TicketStatus


class TicketDAO:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[TICKETS]

    async def insert(self, ticket: Ticket) -> str:
        result = await self.collection.insert_one(ticket.to_mongo())
        return str(result.inserted_id)

    async def find_by_id(self, ticket_id: str) -> Ticket | None:
        doc = await self.collection.find_one({"_id": ObjectId(ticket_id)})
        return Ticket.from_mongo(doc) if doc else None

    async def find_by_customer(self, customer_id: str) -> list[Ticket]:
        cursor = self.collection.find({"customer_id": customer_id}).sort("created_at", -1)
        return [Ticket.from_mongo(doc) async for doc in cursor]

    async def update_status(
        self,
        ticket_id: str,
        status: TicketStatus,
        resolution: str | None = None,
    ) -> bool:
        now = datetime.now(timezone.utc)
        update: dict = {"status": status.value, "updated_at": now}
        if resolution:
            update["resolution"] = resolution
        if status == TicketStatus.RESOLVED:
            update["resolved_at"] = now
        result = await self.collection.update_one(
            {"_id": ObjectId(ticket_id)}, {"$set": update}
        )
        return result.modified_count == 1

    async def escalate(
        self, ticket_id: str, assigned_to: str | None = None
    ) -> bool:
        now = datetime.now(timezone.utc)
        update: dict = {
            "status": TicketStatus.ESCALATED.value,
            "escalated_at": now,
            "updated_at": now,
        }
        if assigned_to:
            update["assigned_to"] = assigned_to
        result = await self.collection.update_one(
            {"_id": ObjectId(ticket_id)}, {"$set": update}
        )
        return result.modified_count == 1
