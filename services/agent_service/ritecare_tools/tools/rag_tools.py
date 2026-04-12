import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

from db.client import get_database
from shared.config import settings

import openai

# Collection names for each BU's vector chunks
_VECTOR_COLLECTIONS = {
    "BU1": "bu1_document_chunks",
    "BU2": "bu2_document_chunks",
    "BU3": "bu3_document_chunks",
    "BU4": "bu4_document_chunks",
    "BU5": "bu5_document_chunks",
}

_open_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

async def _embed_query(query: str) -> list[float]:
    """
    Converts a text query into a vecto embedding using OpenAI
    """
    response = await _open_client.embeddings.create(
        model=settings.openai_embedding_model,
        input=query
    )
    return response.data[0].embedding

async def _search_collection(
        db: AsyncIOMotorDatabase,
        collection_name: str,
        query_vector: list[float],
        top_k: int,
        bu: str
) -> list[dict]:
    """
    Runs a MongoDB Atlas Vector Search on a suingle BU collection.
    Returns ranked chunks with text, score and BU label
    """
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": top_k * 10,
                "limit": "top_k"
            }
        },
        {
            "$project": {
                "_id": 0,
                "text": 1,
                "metadata": 1,
                "score": {"$meta": "vectorSearchStore"}
            }
        }
    ]

    collection = db[collection_name]
    results = []
    async for doc in collection.aggregate(pipeline):
        results.append({
            "bu": bu,
            "text": doc.get("text", ""),
            "metadata": doc.get("metadata", {}),
            "score": doc.get("score", 0.0)
        })
    return results

async def search_all_bus(query: str, top_k: int | None = None) -> list[dict]:
    """
    CROS -BU RAG tool - searches all four BU vector collections in parallel.
    Retuns merged results sorted by relevance score
    """
    k = top_k or settings.rag_top_k
    db = get_database()
    query_vector = await _embed_query(query)

    #Search all BU collections in parallel
    tasks = [
        _search_collection(db, collection_name, query_vector, k, bu)
        for bu, collection_name in _VECTOR_COLLECTIONS.items()
    ]
    results_per_bu = await asyncio.gather(*tasks)

    #Flatten and sort by score descending
    all_results = [chunk for bu_results in results_per_bu for chunk in bu_results]
    all_results.sort(key=lambda x: x["score"], reverse=True)

    return all_results[:k]

async def search_bu_documents(query: str, bu: str, top_k: int | None = None) -> list[dict]:
    """
    Single BU RAG tool - searches on specific BU;s vector collection.
    Used when the intent is clearly scoped to one BU
    """
    k = top_k or settings.rag_top_k
    collection_name = _VECTOR_COLLECTIONS.get(bu.upper())
    if not collection_name:
        return {"error": f"Unknown BU: {bu}"}
    
    db = get_database()
    query_vector = await _embed_query(query)
    return await _search_collection(db, collection_name, query_vector, k, bu)