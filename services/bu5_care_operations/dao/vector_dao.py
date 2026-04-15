from google import genai
from motor.motor_asyncio import AsyncIOMotorDatabase

from common.config import settings
from common.database.collections import BU5_DOCUMENT_CHUNKS

_client = genai.Client(api_key=settings.google_api_key)


class VectorDAO:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[BU5_DOCUMENT_CHUNKS]

    async def search(
        self,
        query: str,
        top_k: int = 5,
        service_type: str | None = None,
    ) -> list[dict]:
        response = _client.models.embed_content(
            model=settings.google_embedding_model,
            contents=query,
        )
        query_vector = response.embeddings[0].values

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
