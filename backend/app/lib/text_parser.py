from io import BytesIO
from pathlib import Path

import fitz
from docx import Document

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def extract_text(content: bytes, filename: str) -> str:
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return _extract_pdf(content)
    if extension == ".docx":
        return _extract_docx(content)

    raise ValueError(f"Unsupported file type: {extension or 'unknown'}")


def get_file_type(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        return "pdf"
    if extension == ".docx":
        return "docx"
    raise ValueError(f"Unsupported file type: {extension or 'unknown'}")


def _extract_pdf(content: bytes) -> str:
    document = fitz.open(stream=content, filetype="pdf")
    try:
        pages = [page.get_text() for page in document]
    finally:
        document.close()

    return "\n".join(pages).strip()


def _extract_docx(content: bytes) -> str:
    document = Document(BytesIO(content))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs).strip()
