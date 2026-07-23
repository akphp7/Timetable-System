"""
Module 1: PDF Ingestion
-----------------------
Extracts text from PDF files and wraps each into a Document object.

How it works:
1. Takes a list of PDF file paths
2. Opens each with pypdf's PdfReader
3. Extracts text page by page
4. Joins all pages into one string per document
5. Returns a list of Document objects (id, filename, text, page_count)

Why this design:
- Each PDF becomes ONE Document (not one per page). We chunk later in Module 2.
- We store source_path so we can cite which file an answer came from.
- doc_id is just the filename (simple, unique enough for our use case).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from pypdf import PdfReader


@dataclass
class Document:
    """Represents one ingested PDF document."""

    doc_id: str           # unique identifier (filename without extension)
    filename: str         # original filename (e.g., "attention_paper.pdf")
    source_path: str      # full path to the PDF file
    text: str             # extracted full text (all pages joined)
    page_count: int       # number of pages in the PDF
    page_texts: List[str] = field(default_factory=list)  # text per page (for page-level citation)


def extract_text_from_pdf(pdf_path: str | Path) -> Document:
    """
    Extract all text from a single PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A Document object containing the extracted text.

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        ValueError: If no text could be extracted.
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    if not path.suffix.lower() == ".pdf":
        raise ValueError(f"Not a PDF file: {path}")

    reader = PdfReader(str(path))
    page_texts = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            page_texts.append(text.strip())
        else:
            page_texts.append("")  # keep page numbering consistent

    full_text = "\n\n".join(page_texts)

    if not full_text.strip():
        raise ValueError(f"No text could be extracted from: {path.name}")

    return Document(
        doc_id=path.stem,                # "attention_paper" from "attention_paper.pdf"
        filename=path.name,              # "attention_paper.pdf"
        source_path=str(path.resolve()), # full absolute path
        text=full_text,
        page_count=len(reader.pages),
        page_texts=page_texts,
    )


def load_pdfs(pdf_paths: List[str | Path]) -> List[Document]:
    """
    Load multiple PDFs and return a list of Documents.

    Args:
        pdf_paths: List of paths to PDF files.

    Returns:
        List of Document objects (one per PDF).

    Skips files that fail to load (prints warning instead of crashing).
    """
    documents = []

    for pdf_path in pdf_paths:
        try:
            doc = extract_text_from_pdf(pdf_path)
            documents.append(doc)
            print(f"  Loaded: {doc.filename} ({doc.page_count} pages, {len(doc.text)} chars)")
        except (FileNotFoundError, ValueError) as e:
            print(f"  Skipped: {e}")

    print(f"\nTotal: {len(documents)} document(s) loaded.")
    return documents
