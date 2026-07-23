from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ..chunking.strategies import Chunker
from ..domain import CorpusState
from ..ingestion import load_pdfs


class DocumentAgent:
    """Ingest PDFs and generate chunks for each configured strategy."""

    def __init__(self, chunkers: Sequence[Chunker]) -> None:
        self._chunkers = list(chunkers)
        if not self._chunkers:
            raise ValueError("At least one chunker is required")

    @property
    def strategies(self) -> list[str]:
        return [chunker.name for chunker in self._chunkers]

    def ingest(self, pdf_paths: Sequence[str | Path]) -> CorpusState:
        documents = load_pdfs(pdf_paths)
        chunks_by_strategy: dict[str, list] = {}

        for chunker in self._chunkers:
            strategy_chunks = []
            for document in documents:
                strategy_chunks.extend(chunker.chunk(document))
            chunks_by_strategy[chunker.name] = strategy_chunks

        return CorpusState(documents=documents, chunks_by_strategy=chunks_by_strategy)
