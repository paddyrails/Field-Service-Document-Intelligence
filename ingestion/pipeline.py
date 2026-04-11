import os
from datetime import datetime, timezone

from shared.config import settings
from db.client import get_database
from ingestion.chunker import chunk_text
from ingestion.embedder import embed_chunks
from ingestion.loaders.pdf_loader import load_pdf
from ingestion.loaders.text_loader import load_text

async def run_pipeline(
        file_path:str,
        collection_name: str,
        metadata: dict | None = None
) -> int:
    """
    Full ingestion pipeline:
    load -> chunk -> embed -> store in MongoDB

    Args:
        file_path: path to uploaded file (PDF or txt/md)
        collection_name: MongoDB collection to store chunks in
        metadata: optional extra fields stored with each chunk. (e.g customer_id, source filename, bu)

    Returns:
        Number of chunks stored.        
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
    
    chunks = chunk_text(
        text,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap
    )

    embeddings = await embed_chunks(chunks)

    now = datetime.now(timezone.utc)
    source_filename = os.path.basename(file_path)
    base_metadata = {
        "source": source_filename,
        "ingested_at": now,
        **(metadata or {})
    }

    documents = [
        {
            "text": chunk,
            "embedding": embedding,
            "metadata": base_metadata,
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]

    #5 Store in MongoDB
    db = get_database()
    collection =  db[collection_name]
    await collection.insert_many(documents)

    return len(documents)



