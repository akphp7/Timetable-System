from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkingConfig:
    """Character-level defaults for chunking experiments."""

    fixed_chunk_size: int = 1200
    overlap_chunk_size: int = 1200
    overlap_size: int = 400
    semantic_max_chunk_size: int = 1400
    semantic_min_chunk_size: int = 600
    semantic_similarity_threshold: float = 0.18


@dataclass(frozen=True)
class EngineConfig:
    """Runtime settings for a single-user run."""

    top_k: int = 4
    random_seed: int = 42
    mastery_decay: float = 0.15
