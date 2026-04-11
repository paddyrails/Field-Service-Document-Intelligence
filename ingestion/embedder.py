import asyncio

import openai

from shared.config import settings

_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

BATCH_SIZE = 20

async def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """
    Converts a list of text chunks into embedding vectors.
    Processes in batches of 2- to rester OpenAI rate limits.
    Retunrs a list of 1536-dimension float vectors
    """
    all_embeddings: list[list[float]] = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        response = await _client.embeddings.create(
            model=settings.openai_embedding_model,
            input=batch
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

        # Small pause between batches to avoid rate limit errors
        if i + BATCH_SIZE < len(chunks):
            await asyncio.sleep(0.5)

    return all_embeddings