from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from common.database.collections import BU1_DOCUMENT_CHUNKS
from common.models.document_chunk import DocumentChunk

class VectorDAO:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[BU1_DOCUMENT_CHUNKS]

    async def insert_chunk(self, chunk: DocumentChunk) -> str:
        result = await self.collection.insert_one(chunk.to_mongo())
        return str(result.inserted_id)
    
    async def search(
            self,
            query_vector: list[float],
            top_k: int = 5,
            customer_id: str | None = None
    ) -> list[dict]:
        pipeline: list[dict] = [
            {
                "$vectorSearch": {
                    "index": "bu1_vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": top_k*10,
                    "limit": top_k,
                    **({"filter": {"customer_id": customer_id}} if customer_id else {})
                },
                
            },
            {
                "$project": {
                    "text":1,
                    "source":1,
                    "score": {
                        "$meta": "vectorSearchScore"
                    }
                }
            }
        ]
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=top_k)
        