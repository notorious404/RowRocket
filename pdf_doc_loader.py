# pdf_doc_loader.py
import os
from typing import Dict
from PyPDF2 import PdfReader
from docx import Document

from utils import ensure_directories

def read_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)

def read_docx_text(path: str) -> str:
    doc = Document(path)
    parts = []
    for p in doc.paragraphs:
        parts.append(p.text)
    return "\n".join(parts)

def save_and_read_uploaded_files(uploaded_files) -> Dict[str, str]:
    """
    Saves uploaded files into input_pdfs/ (as requested)
    and returns {file_path: extracted_text}.
    """
    ensure_directories()
    result = {}
    for uf in uploaded_files:
        filename = uf.name
        ext = os.path.splitext(filename)[1].lower()
        save_path = os.path.join("input_pdfs", filename)

        with open(save_path, "wb") as f:
            f.write(uf.read())

        if ext == ".pdf":
            text = read_pdf_text(save_path)
        elif ext in (".docx", ".doc"):
            # basic DOCX support; for .doc you may convert externally
            text = read_docx_text(save_path)
        else:
            text = ""

        result[save_path] = text
    return result
