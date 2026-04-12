import openai
import os

_client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

async def embed_chunks(
    chunks: list[str],
    bu: str,
    customer_id: str,
    service_type: str = "",
) -> list[dict]:
    response = await _client.embeddings.create(
        model="text-embedding-3-small",
        input=chunks
    )

    return [
        {
            "text": chunks[i],
            "embedding": response.data[i].embedding,
            "metadata": {
                "bu": bu,
                "customer_id": customer_id,
                "chunk_index": i,
                **({"service_type": service_type} if service_type else {}),
            },
        }
        for i in range(len(chunks))
    ]
