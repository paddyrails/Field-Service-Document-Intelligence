from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from common.database.collections import CUSTOMERS
from common.models.customer import Customer, KYCStatus, OnboardingStage

class CustomerDAO:

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[CUSTOMERS]

    async def insert(self, customer: Customer) -> str:
        result = await self.collection.insert_one(customer.to_mongo())
        return str(result.inserted_id)

    async def find_by_id(self, customer_id: str) -> Customer:
        doc = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if doc is None:
            return None
        return Customer.from_mongo(doc)
    
    async def find_by_email(self, email: str) -> Customer | None:
        doc = await self.collection.find_one({"email": email})
        if doc is None:
            return None
        return Customer.from_mongo(doc)


    async def update_kyc(
            self, customer_id: str, kyc_status: KYCStatus, kyc_notes: str
    ) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(customer_id)},
            {
                "$set": {
                    "kyc_status": kyc_status.value,
                    "kyc_notes": kyc_notes,
                    "updated_at": datetime.now(timezone.utc)

                }
            }
        )
        return result.modified_count == 1
    
    async def update_onboarding_stage(self, customer_id: str, stage: OnboardingStage) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(customer_id)},
            {
                "$set": {
                    "onboarding_stage": stage.value,
                    "updated_at": datetime.now(timezone.utc)
                }
          }
        )
        return result.modified_count == 1

    
    
