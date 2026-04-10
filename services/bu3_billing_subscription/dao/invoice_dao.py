from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.collections import INVOICES
from common.models.invoice import Invoice, InvoiceStatus


class InvoiceDAO:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[INVOICES]

    async def insert(self, invoice: Invoice) -> str:
        result = await self.collection.insert_one(invoice.to_mongo())
        return str(result.inserted_id)

    async def find_by_id(self, invoice_id: str) -> Invoice | None:
        doc = await self.collection.find_one({"_id": ObjectId(invoice_id)})
        return Invoice.from_mongo(doc) if doc else None

    async def find_by_customer(self, customer_id: str) -> list[Invoice]:
        cursor = self.collection.find({"customer_id": customer_id}).sort("created_at", -1)
        return [Invoice.from_mongo(doc) async for doc in cursor]

    async def mark_paid(self, invoice_id: str) -> bool:
        now = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"_id": ObjectId(invoice_id)},
            {"$set": {"status": InvoiceStatus.PAID.value, "paid_at": now, "updated_at": now}},
        )
        return result.modified_count == 1
