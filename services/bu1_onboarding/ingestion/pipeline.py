import os
from datetime import datetime, timezone

from common.config import settings
from ingestion.chunker import chunk_text
from ingestion.embedder import embed_chunks
from ingestion.loaders.pdf_loader import load_pdf
from ingestion.loaders.text_loader import load_text


async def run_pipeline(
    file_path: str,
    metadata: dict | None = None,
) -> list[dict]:
    """
    Runs the full ingestion pipeline on a single file.
    load -> chunk -> embed -> return documents

    Does NOT insert into MongoDB.
    The service layer handles persistence via VectorDAO.

    Args:
        file_path: path to the file (PDF or txt/md)
        metadata:  optional fields stored with each chunk
                   (e.g. customer_id, source_filename, bu, type)

    Returns:
        List of documents ready for insertion:
        [{"text": "...", "embedding": [...], "metadata": {...}}]
    """
    # 1. Load raw text based on file type
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        text = load_pdf(file_path)
    elif ext in (".txt", ".md"):
        text = load_text(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .txt, .md")

    if not text.strip():
        raise ValueError("File contains no extractable text")

    # 2. Split into chunks
    chunks = chunk_text(
        text,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )

    # 3. Embed all chunks
    embeddings = await embed_chunks(chunks)

    # 4. Build and return documents
    now = datetime.now(timezone.utc)
    base_metadata = {
        "source": os.path.basename(file_path),
        "ingested_at": now,
        **(metadata or {}),
    }

    return [
        {
            "text": chunk,
            "embedding": embedding,
            "metadata": base_metadata,
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]
