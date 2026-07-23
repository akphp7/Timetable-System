from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Document:
    doc_id: str
    title: str
    source_path: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    start: int
    end: int
    strategy: str
    source_path: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CorpusState:
    documents: list[Document]
    chunks_by_strategy: dict[str, list[Chunk]]


@dataclass(slots=True)
class RetrievalResult:
    chunk: Chunk
    score: float


@dataclass(slots=True)
class Citation:
    chunk_id: str
    doc_id: str
    source_path: str
    score: float


@dataclass(slots=True)
class AgentAnswer:
    question: str
    answer: str
    strategy: str
    citations: list[Citation]


@dataclass(slots=True)
class Flashcard:
    prompt: str
    answer: str
    source_chunk_id: str


@dataclass(slots=True)
class QuizQuestion:
    question_id: str
    prompt: str
    options: list[str]
    correct_option: int
    explanation: str
    source_chunk_id: str


@dataclass(slots=True)
class QuizResult:
    score: int
    total: int
    accuracy: float
