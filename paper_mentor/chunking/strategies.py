from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from ..domain import Chunk, Document

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


class Chunker(Protocol):
    name: str

    def chunk(self, document: Document) -> list[Chunk]:
        ...


def _build_chunk(
    document: Document,
    strategy: str,
    index: int,
    text: str,
    start: int,
    end: int,
) -> Chunk:
    return Chunk(
        chunk_id=f"{document.doc_id}_{strategy}_{index:04d}",
        doc_id=document.doc_id,
        text=text,
        start=start,
        end=end,
        strategy=strategy,
        source_path=document.source_path,
    )


def _window_chunk(
    document: Document,
    strategy: str,
    chunk_size: int,
    stride: int,
) -> list[Chunk]:
    text = document.text
    if not text.strip():
        return []

    chunk_size = max(200, chunk_size)
    stride = max(1, stride)
    chunks: list[Chunk] = []

    start = 0
    index = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        snippet = text[start:end].strip()
        if snippet:
            chunks.append(_build_chunk(document, strategy, index, snippet, start, end))
            index += 1

        if end >= text_len:
            break
        start += stride

    return chunks


@dataclass(slots=True)
class FixedSizeChunker:
    chunk_size: int = 1200
    name: str = "fixed"

    def chunk(self, document: Document) -> list[Chunk]:
        return _window_chunk(
            document=document,
            strategy=self.name,
            chunk_size=self.chunk_size,
            stride=self.chunk_size,
        )


@dataclass(slots=True)
class OverlappingChunker:
    chunk_size: int = 1200
    overlap_size: int = 400
    name: str = "overlap"

    def chunk(self, document: Document) -> list[Chunk]:
        overlap_size = max(0, min(self.overlap_size, self.chunk_size - 1))
        stride = self.chunk_size - overlap_size
        return _window_chunk(
            document=document,
            strategy=self.name,
            chunk_size=self.chunk_size,
            stride=stride,
        )


@dataclass(slots=True)
class SemanticChunker:
    max_chunk_size: int = 1400
    min_chunk_size: int = 600
    similarity_threshold: float = 0.18
    name: str = "semantic"

    def _sentence_similarity(self, left: str, right: str) -> float:
        left_tokens = {t.lower() for t in _TOKEN_RE.findall(left) if len(t) > 2}
        right_tokens = {t.lower() for t in _TOKEN_RE.findall(right) if len(t) > 2}
        if not left_tokens or not right_tokens:
            return 0.0
        intersection = len(left_tokens & right_tokens)
        union = len(left_tokens | right_tokens)
        return intersection / union if union else 0.0

    def chunk(self, document: Document) -> list[Chunk]:
        text = document.text.strip()
        if not text:
            return []

        sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
        if not sentences:
            return []

        chunks: list[Chunk] = []
        cursor = 0
        chunk_index = 0

        current_sentences: list[str] = []
        current_start = 0
        current_end = 0
        current_len = 0

        for sentence in sentences:
            sentence_start = text.find(sentence, cursor)
            if sentence_start == -1:
                sentence_start = cursor
            sentence_end = sentence_start + len(sentence)
            cursor = sentence_end

            if not current_sentences:
                current_sentences = [sentence]
                current_start = sentence_start
                current_end = sentence_end
                current_len = len(sentence)
                continue

            similarity = self._sentence_similarity(current_sentences[-1], sentence)
            proposed_len = current_len + 1 + len(sentence)

            should_split = (
                proposed_len > self.max_chunk_size
                or (
                    current_len >= self.min_chunk_size
                    and similarity < self.similarity_threshold
                )
            )

            if should_split:
                chunk_text = " ".join(current_sentences).strip()
                if chunk_text:
                    chunks.append(
                        _build_chunk(
                            document=document,
                            strategy=self.name,
                            index=chunk_index,
                            text=chunk_text,
                            start=current_start,
                            end=current_end,
                        )
                    )
                    chunk_index += 1

                current_sentences = [sentence]
                current_start = sentence_start
                current_end = sentence_end
                current_len = len(sentence)
            else:
                current_sentences.append(sentence)
                current_end = sentence_end
                current_len = proposed_len

        if current_sentences:
            chunk_text = " ".join(current_sentences).strip()
            if chunk_text:
                chunks.append(
                    _build_chunk(
                        document=document,
                        strategy=self.name,
                        index=chunk_index,
                        text=chunk_text,
                        start=current_start,
                        end=current_end,
                    )
                )

        return chunks
