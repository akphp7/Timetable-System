from __future__ import annotations

from typing import Sequence

from ..domain import Chunk, RetrievalResult

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # pragma: no cover - dependency check
    TfidfVectorizer = None
    cosine_similarity = None


class TfidfVectorStore:
    """Small, in-memory TF-IDF index for single-user experiments."""

    def __init__(self) -> None:
        self._vectorizer = None
        self._matrix = None
        self._chunks: list[Chunk] = []

    @property
    def size(self) -> int:
        return len(self._chunks)

    def build(self, chunks: Sequence[Chunk]) -> None:
        if TfidfVectorizer is None:
            raise ImportError(
                "scikit-learn is required. Install with: pip install scikit-learn"
            )

        self._chunks = list(chunks)
        if not self._chunks:
            self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            self._matrix = None
            return

        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        corpus = [chunk.text for chunk in self._chunks]
        self._matrix = self._vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 4) -> list[RetrievalResult]:
        if not query.strip() or self._matrix is None or self._vectorizer is None:
            return []
        if cosine_similarity is None:
            raise ImportError(
                "scikit-learn is required. Install with: pip install scikit-learn"
            )

        query_vec = self._vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self._matrix)[0]

        ranked_indices = sorted(
            range(len(similarities)),
            key=lambda idx: float(similarities[idx]),
            reverse=True,
        )

        results: list[RetrievalResult] = []
        for idx in ranked_indices[: max(1, top_k)]:
            score = float(similarities[idx])
            if score <= 0:
                continue
            results.append(RetrievalResult(chunk=self._chunks[idx], score=score))

        return results
