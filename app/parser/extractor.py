"""Extract raw text from resume files (PDF / DOCX)."""

from typing import BinaryIO

import pdfplumber
from docx import Document
from werkzeug.datastructures import FileStorage


def extract_text_from_pdf(stream: BinaryIO) -> str:
    """Pull text from every page of a PDF using pdfplumber."""
    with pdfplumber.open(stream) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages).strip()


def extract_text_from_docx(stream: BinaryIO) -> str:
    """Pull text from paragraphs and tables of a DOCX document."""
    document = Document(stream)
    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]

    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    return "\n".join(parts).strip()


def extract_text(file_storage: FileStorage) -> str:
    """Dispatch to the right extractor based on the uploaded filename."""
    filename = (file_storage.filename or "").lower()
    stream = file_storage.stream

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(stream)
    elif filename.endswith((".doc", ".docx")):
        # python-docx reads .docx; legacy .doc is best-effort only.
        text = extract_text_from_docx(stream)
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    if not text:
        raise ValueError("No readable text found in the document (it may be scanned)")

    return text
