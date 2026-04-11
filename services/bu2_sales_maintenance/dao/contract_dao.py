from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.collections import CONTRACTS
from common.models.contract import Contract, ContractStatus


class ContractDAO:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[CONTRACTS]

    async def insert(self, contract: Contract) -> str:
        result = await self.collection.insert_one(contract.to_mongo())
        return str(result.inserted_id)

    async def find_by_id(self, contract_id: str) -> Contract | None:
        doc = await self.collection.find_one({"_id": ObjectId(contract_id)})
        return Contract.from_mongo(doc) if doc else None

    async def find_by_customer(self, customer_id: str) -> list[Contract]:
        cursor = self.collection.find({"customer_id": customer_id}).sort("created_at", -1)
        return [Contract.from_mongo(doc) async for doc in cursor]

    async def update_status(self, contract_id: str, status: ContractStatus) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(contract_id)},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.modified_count == 1
