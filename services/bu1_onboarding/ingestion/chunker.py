import tiktoken

def chunk_text(text: str, chunk_size: int = 500,chunk_overlap: int = 50) -> list[str]:
    """
    Splits text line into overlapping chunks measured in tokens.
    Returns a list of text chunk strings.
    """
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(text)
    chunks = []
    start =0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoder.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += chunk_size - chunk_overlap

    return chunks