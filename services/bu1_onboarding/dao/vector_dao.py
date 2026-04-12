from motor.motor_asyncio import AsyncIOMotorDatabase

from common.database.collections import BU1_DOCUMENT_CHUNKS


class VectorDAO:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[BU1_DOCUMENT_CHUNKS]

    async def insert_chunks(self, documents: list[dict]) -> int:
        """
        Batch inserts a list of chunk documents into the vector collection.
        Each document must have: text, embedding, metadata.
        Returns number of inserted documents.
        """
        if not documents:
            return 0
        result = await self.collection.insert_many(documents)
        return len(result.inserted_ids)

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Runs MongoDB Atlas Vector Search using cosine similarity.
        Returns top_k most relevant chunks with text, metadata and score.
        """
        vector_search_stage: dict = {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": top_k * 10,
                "limit": top_k,
            }
        }

        if filters:
            vector_search_stage["$vectorSearch"]["filter"] = filters

        pipeline = [
            vector_search_stage,
            {
                "$project": {
                    "_id": 0,
                    "text": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        results = []
        async for doc in self.collection.aggregate(pipeline):
            results.append(doc)
        return results
