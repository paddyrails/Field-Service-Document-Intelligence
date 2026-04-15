from google import genai

from common.config import settings

_client = genai.Client(api_key=settings.google_api_key)

BATCH_SIZE = 20


async def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """
    Converts a list of text chunks into embedding vectors.
    Processes in batches of 20 to respect rate limits.
    Returns a list of 768-dimension float vectors.
    """
    all_embeddings: list[list[float]] = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        response = _client.models.embed_content(
            model=settings.google_embedding_model,
            contents=batch,
        )
        batch_embeddings = [e.values for e in response.embeddings]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings
