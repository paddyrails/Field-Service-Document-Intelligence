from pypdf import PdfReader

def load_pdf(file_path: str) -> str:
    """
    Extracts and returns all text from a PDF file.
    Pages are joined with a newline separator
    """
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if(text):
            pages.append(text.strip())
    return "\n".join(pages)