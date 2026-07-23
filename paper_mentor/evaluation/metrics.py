from __future__ import annotations

import math
from statistics import mean
from typing import Mapping

from ..retrieval.tfidf_store import TfidfVectorStore


def recall_at_k(relevant_doc_ids: set[str], retrieved_doc_ids: list[str], k: int) -> float:
    if not relevant_doc_ids:
        return 0.0
    top = retrieved_doc_ids[: max(1, k)]
    hits = len(set(top) & relevant_doc_ids)
    return hits / len(relevant_doc_ids)


def ndcg_at_k(
    relevance_by_doc_id: Mapping[str, float],
    retrieved_doc_ids: list[str],
    k: int,
) -> float:
    if not relevance_by_doc_id:
        return 0.0

    k = max(1, k)

    def dcg(doc_ids: list[str]) -> float:
        score = 0.0
        for rank, doc_id in enumerate(doc_ids[:k], start=1):
            rel = relevance_by_doc_id.get(doc_id, 0.0)
            if rel <= 0:
                continue
            score += rel / math.log2(rank + 1)
        return score

    ideal_docs = sorted(
        relevance_by_doc_id.keys(),
        key=lambda doc_id: relevance_by_doc_id[doc_id],
        reverse=True,
    )

    ideal = dcg(ideal_docs)
    if ideal == 0:
        return 0.0
    return dcg(retrieved_doc_ids) / ideal


def evaluate_strategies(
    stores: Mapping[str, TfidfVectorStore],
    query_relevance_map: Mapping[str, set[str]],
    top_k: int = 5,
) -> dict[str, dict[str, float]]:
    """Evaluate retrieval quality for each strategy using doc-level relevance."""

    report: dict[str, dict[str, float]] = {}

    for strategy, store in stores.items():
        recalls: list[float] = []
        ndcgs: list[float] = []

        for query, relevant_doc_ids in query_relevance_map.items():
            results = store.search(query, top_k=top_k)
            retrieved_doc_ids = [result.chunk.doc_id for result in results]
            recalls.append(recall_at_k(relevant_doc_ids, retrieved_doc_ids, top_k))
            relevance = {doc_id: 1.0 for doc_id in relevant_doc_ids}
            ndcgs.append(ndcg_at_k(relevance, retrieved_doc_ids, top_k))

        report[strategy] = {
            "recall_at_k": mean(recalls) if recalls else 0.0,
            "ndcg_at_k": mean(ndcgs) if ndcgs else 0.0,
            "num_queries": float(len(query_relevance_map)),
            "index_size": float(store.size),
        }

    return report
