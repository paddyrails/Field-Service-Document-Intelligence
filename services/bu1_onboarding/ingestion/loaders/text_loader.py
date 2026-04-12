def load_text(file_path: str) -> str:
    """
    Reads and return the contents of a plain text or markdown file
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()