from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from .agents import AssessmentAgent, DocumentAgent, TutorAgent
from .chunking import FixedSizeChunker, OverlappingChunker, SemanticChunker
from .config import ChunkingConfig, EngineConfig
from .domain import AgentAnswer, CorpusState, Flashcard, QuizQuestion, QuizResult
from .evaluation import evaluate_strategies


class PaperMentorEngine:
    """Single-user modular engine for research paper learning workflows."""

    def __init__(
        self,
        engine_config: EngineConfig | None = None,
        chunking_config: ChunkingConfig | None = None,
    ) -> None:
        self._engine_config = engine_config or EngineConfig()
        self._chunking_config = chunking_config or ChunkingConfig()

        chunkers = [
            FixedSizeChunker(chunk_size=self._chunking_config.fixed_chunk_size),
            OverlappingChunker(
                chunk_size=self._chunking_config.overlap_chunk_size,
                overlap_size=self._chunking_config.overlap_size,
            ),
            SemanticChunker(
                max_chunk_size=self._chunking_config.semantic_max_chunk_size,
                min_chunk_size=self._chunking_config.semantic_min_chunk_size,
                similarity_threshold=self._chunking_config.semantic_similarity_threshold,
            ),
        ]

        self.document_agent = DocumentAgent(chunkers=chunkers)
        self.tutor_agent = TutorAgent(default_top_k=self._engine_config.top_k)
        self.assessment_agent = AssessmentAgent(seed=self._engine_config.random_seed)
        self._corpus: CorpusState | None = None

    def ingest_pdfs(self, pdf_paths: Sequence[str | Path]) -> dict[str, int]:
        self._corpus = self.document_agent.ingest(pdf_paths)
        self.tutor_agent.index(self._corpus)
        return {
            strategy: len(chunks)
            for strategy, chunks in self._corpus.chunks_by_strategy.items()
        }

    def available_strategies(self) -> list[str]:
        self._assert_ready()
        return self.tutor_agent.available_strategies()

    def ask(
        self,
        question: str,
        strategy: str = "overlap",
        top_k: int | None = None,
    ) -> AgentAnswer:
        self._assert_ready()
        return self.tutor_agent.answer_question(question, strategy, top_k)

    def make_flashcards(
        self,
        topic: str,
        strategy: str = "overlap",
        count: int = 5,
    ) -> list[Flashcard]:
        self._assert_ready()
        return self.tutor_agent.generate_flashcards(topic, strategy, count)

    def create_quiz(
        self,
        topic: str,
        strategy: str = "overlap",
        num_questions: int = 5,
    ) -> list[QuizQuestion]:
        self._assert_ready()

        mastery = self.assessment_agent.get_mastery(topic)
        adjusted_num_questions = num_questions + 1 if mastery < 0.4 else num_questions

        retrieval = self.tutor_agent.retrieve(
            topic,
            strategy,
            top_k=max(adjusted_num_questions, self._engine_config.top_k),
        )
        return self.assessment_agent.generate_quiz(
            topic,
            retrieval_results=retrieval,
            num_questions=adjusted_num_questions,
        )

    def submit_quiz(
        self,
        topic: str,
        questions: list[QuizQuestion],
        user_answers: list[int],
    ) -> QuizResult:
        result = self.assessment_agent.grade_quiz(questions, user_answers)
        self.assessment_agent.update_mastery(
            topic,
            result,
            decay=self._engine_config.mastery_decay,
        )
        return result

    def benchmark_chunking(
        self,
        query_relevance_map: Mapping[str, set[str]],
        top_k: int = 5,
    ) -> dict[str, dict[str, float]]:
        self._assert_ready()
        stores = self.tutor_agent.strategy_stores()
        return evaluate_strategies(
            stores=stores,
            query_relevance_map=query_relevance_map,
            top_k=top_k,
        )

    def ablation_report(
        self,
        query_relevance_map: Mapping[str, set[str]],
        top_k: int = 5,
        reference_strategy: str = "overlap",
    ) -> dict[str, dict[str, float]]:
        """Return strategy metrics and delta vs a reference strategy."""

        metrics = self.benchmark_chunking(query_relevance_map, top_k=top_k)
        if reference_strategy not in metrics:
            return metrics

        baseline = metrics[reference_strategy]
        output: dict[str, dict[str, float]] = {}

        for strategy, values in metrics.items():
            output[strategy] = dict(values)
            output[strategy]["delta_recall_vs_reference"] = (
                values["recall_at_k"] - baseline["recall_at_k"]
            )
            output[strategy]["delta_ndcg_vs_reference"] = (
                values["ndcg_at_k"] - baseline["ndcg_at_k"]
            )

        return output

    def _assert_ready(self) -> None:
        if self._corpus is None:
            raise RuntimeError("Call ingest_pdfs(...) before querying the engine")
