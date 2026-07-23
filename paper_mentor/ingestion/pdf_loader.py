from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Sequence

from ..domain import Document

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency check
    PdfReader = None


_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _build_doc_id(path: Path, text: str) -> str:
    payload = f"{path.resolve()}::{len(text)}::{text[:500]}"
    digest = hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()[:12]
    return f"doc_{digest}"


def load_pdf(path: str | Path) -> Document:
    """Load a single PDF and return one normalized Document object."""

    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if PdfReader is None:
        raise ImportError("pypdf is required. Install with: pip install pypdf")

    reader = PdfReader(str(pdf_path))
    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        normalized = _normalize_whitespace(text)
        if normalized:
            pages.append(normalized)

    full_text = "\n".join(pages).strip()
    if not full_text:
        raise ValueError(f"No extractable text found in: {pdf_path}")

    metadata = reader.metadata or {}
    title = ""
    if hasattr(metadata, "get"):
        title = str(metadata.get("/Title", "")).strip()

    if not title:
        title = pdf_path.stem

    return Document(
        doc_id=_build_doc_id(pdf_path, full_text),
        title=title,
        source_path=str(pdf_path),
        text=full_text,
        metadata={"num_pages": len(reader.pages)},
    )


def load_pdfs(paths: Sequence[str | Path]) -> list[Document]:
    """Load multiple PDFs in deterministic order."""

    documents: list[Document] = []
    for path in paths:
        documents.append(load_pdf(path))
    return documents
