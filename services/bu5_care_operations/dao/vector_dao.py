import openai
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.config import settings
from common.database.collections import BU5_DOCUMENT_CHUNKS

_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)


class VectorDAO:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[BU5_DOCUMENT_CHUNKS]

    async def search(
        self,
        query: str,
        top_k: int = 5,
        service_type: str | None = None,
    ) -> list[dict]:
        response = await _client.embeddings.create(
            model=settings.openai_embedding_model,
            input=query,
        )
        query_vector = response.data[0].embedding

        pipeline: list[dict] = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                    **({"filter": {"metadata.service_type": service_type}} if service_type else {}),
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "text": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        return [doc async for doc in self.collection.aggregate(pipeline)]
