import os
from google import genai

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

BATCH_SIZE = 100  # Google API limit


def embed_chunks(
    chunks: list[str],
    bu: str,
    customer_id: str,
    service_type: str = "",
) -> list[dict]:
    all_embeddings: list[list[float]] = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=batch,
        )
        all_embeddings.extend([e.values for e in response.embeddings])

    return [
        {
            "text": chunks[i],
            "embedding": all_embeddings[i],
            "metadata": {
                "bu": bu,
                "customer_id": customer_id,
                "chunk_index": i,
                **({"service_type": service_type} if service_type else {}),
            },
        }
        for i in range(len(chunks))
    ]
