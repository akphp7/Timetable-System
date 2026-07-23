from __future__ import annotations

import re
from typing import Iterable

from ..domain import AgentAnswer, Citation, CorpusState, Flashcard, RetrievalResult
from ..retrieval import TfidfVectorStore

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


class TutorAgent:
    """Answer questions and generate flashcards from retrieved evidence."""

    def __init__(self, default_top_k: int = 4) -> None:
        self._default_top_k = max(1, default_top_k)
        self._stores: dict[str, TfidfVectorStore] = {}

    def index(self, corpus: CorpusState) -> None:
        self._stores = {}
        for strategy, chunks in corpus.chunks_by_strategy.items():
            store = TfidfVectorStore()
            store.build(chunks)
            self._stores[strategy] = store

    def available_strategies(self) -> list[str]:
        return sorted(self._stores.keys())

    def strategy_stores(self) -> dict[str, TfidfVectorStore]:
        return dict(self._stores)

    def retrieve(
        self,
        query: str,
        strategy: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        if strategy not in self._stores:
            raise ValueError(f"Unknown strategy: {strategy}")
        return self._stores[strategy].search(query, top_k or self._default_top_k)

    def answer_question(
        self,
        question: str,
        strategy: str,
        top_k: int | None = None,
    ) -> AgentAnswer:
        results = self.retrieve(question, strategy, top_k)
        answer = self._extractive_answer(question, results)
        citations = [
            Citation(
                chunk_id=result.chunk.chunk_id,
                doc_id=result.chunk.doc_id,
                source_path=result.chunk.source_path,
                score=result.score,
            )
            for result in results
        ]

        return AgentAnswer(
            question=question,
            answer=answer,
            strategy=strategy,
            citations=citations,
        )

    def generate_flashcards(
        self,
        topic: str,
        strategy: str,
        count: int = 5,
    ) -> list[Flashcard]:
        results = self.retrieve(topic, strategy, top_k=max(count, self._default_top_k))
        cards: list[Flashcard] = []

        for result in results:
            key_sentence = self._best_sentence(topic, result.chunk.text)
            keyword = self._pick_keyword(key_sentence)
            if not keyword:
                continue
            cards.append(
                Flashcard(
                    prompt=f"What does '{keyword}' refer to in this paper context?",
                    answer=key_sentence,
                    source_chunk_id=result.chunk.chunk_id,
                )
            )
            if len(cards) >= count:
                break

        return cards

    def _extractive_answer(
        self,
        question: str,
        results: Iterable[RetrievalResult],
    ) -> str:
        query_terms = {t.lower() for t in _TOKEN_RE.findall(question) if len(t) > 2}
        candidates: list[tuple[float, str]] = []

        for result in results:
            for sentence in _SENTENCE_RE.split(result.chunk.text):
                sentence = sentence.strip()
                if len(sentence) < 40:
                    continue
                sentence_terms = {
                    t.lower() for t in _TOKEN_RE.findall(sentence) if len(t) > 2
                }
                overlap = len(query_terms & sentence_terms)
                score = result.score + (0.03 * overlap)
                candidates.append((score, sentence))

        if not candidates:
            return "No grounded answer could be generated from the indexed PDFs."

        ordered = sorted(candidates, key=lambda item: item[0], reverse=True)
        selected: list[str] = []
        seen: set[str] = set()

        for _, sentence in ordered:
            normalized = sentence.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            selected.append(sentence)
            if len(selected) == 3:
                break

        return " ".join(selected)

    def _best_sentence(self, topic: str, text: str) -> str:
        query_terms = {t.lower() for t in _TOKEN_RE.findall(topic) if len(t) > 2}
        best_sentence = ""
        best_score = -1

        for sentence in _SENTENCE_RE.split(text):
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
            sentence_terms = {t.lower() for t in _TOKEN_RE.findall(sentence) if len(t) > 2}
            overlap = len(query_terms & sentence_terms)
            if overlap > best_score:
                best_score = overlap
                best_sentence = sentence

        return best_sentence or text[:200].strip()

    def _pick_keyword(self, sentence: str) -> str:
        candidates = [token for token in _TOKEN_RE.findall(sentence) if len(token) > 5]
        if not candidates:
            return ""
        return max(candidates, key=len)
