from __future__ import annotations

import random
import re
from typing import Iterable

from ..domain import QuizQuestion, QuizResult, RetrievalResult

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


class AssessmentAgent:
    """Generate quizzes and maintain simple topic mastery for one user."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self._mastery_by_topic: dict[str, float] = {}

    def get_mastery(self, topic: str) -> float:
        return self._mastery_by_topic.get(topic.strip().lower(), 0.0)

    def generate_quiz(
        self,
        topic: str,
        retrieval_results: Iterable[RetrievalResult],
        num_questions: int = 5,
    ) -> list[QuizQuestion]:
        num_questions = max(1, num_questions)
        sentences = self._collect_candidate_sentences(retrieval_results)
        if not sentences:
            return []

        term_pool = self._build_term_pool(sentences)
        questions: list[QuizQuestion] = []

        for index in range(num_questions):
            sentence = sentences[index % len(sentences)]
            answer_term = self._pick_answer_term(sentence, term_pool)
            if not answer_term:
                continue

            prompt = self._build_cloze_prompt(topic, sentence, answer_term)
            options, correct_index = self._build_options(answer_term, term_pool)
            question = QuizQuestion(
                question_id=f"q_{index + 1:02d}",
                prompt=prompt,
                options=options,
                correct_option=correct_index,
                explanation=sentence,
                source_chunk_id="generated_from_retrieval",
            )
            questions.append(question)

        return questions

    def grade_quiz(
        self,
        questions: list[QuizQuestion],
        user_answers: list[int],
    ) -> QuizResult:
        total = len(questions)
        if total == 0:
            return QuizResult(score=0, total=0, accuracy=0.0)

        score = 0
        for idx, question in enumerate(questions):
            if idx < len(user_answers) and user_answers[idx] == question.correct_option:
                score += 1

        accuracy = score / total
        return QuizResult(score=score, total=total, accuracy=accuracy)

    def update_mastery(
        self,
        topic: str,
        quiz_result: QuizResult,
        decay: float = 0.15,
    ) -> float:
        key = topic.strip().lower()
        previous = self._mastery_by_topic.get(key, 0.0)

        decay = min(max(decay, 0.01), 1.0)
        updated = previous * (1 - decay) + (quiz_result.accuracy * decay)
        self._mastery_by_topic[key] = updated
        return updated

    def _collect_candidate_sentences(
        self,
        retrieval_results: Iterable[RetrievalResult],
    ) -> list[str]:
        candidates: list[str] = []
        for result in retrieval_results:
            for sentence in _SENTENCE_RE.split(result.chunk.text):
                sentence = sentence.strip()
                if len(sentence) >= 45:
                    candidates.append(sentence)

        if not candidates:
            for result in retrieval_results:
                fallback = result.chunk.text.strip()
                if fallback:
                    candidates.append(fallback[:220])
        return candidates

    def _build_term_pool(self, sentences: list[str]) -> list[str]:
        terms = {
            token
            for sentence in sentences
            for token in _TOKEN_RE.findall(sentence)
            if len(token) >= 5
        }
        return sorted(terms)

    def _pick_answer_term(self, sentence: str, term_pool: list[str]) -> str:
        local_terms = [term for term in _TOKEN_RE.findall(sentence) if len(term) >= 5]
        if local_terms:
            return max(local_terms, key=len)
        return term_pool[0] if term_pool else ""

    def _build_cloze_prompt(self, topic: str, sentence: str, answer_term: str) -> str:
        replaced = sentence.replace(answer_term, "_____", 1)
        return f"[{topic}] Fill in the blank: {replaced}"

    def _build_options(self, answer_term: str, term_pool: list[str]) -> tuple[list[str], int]:
        distractors = [term for term in term_pool if term.lower() != answer_term.lower()]
        self._rng.shuffle(distractors)
        selected = distractors[:3]

        while len(selected) < 3:
            selected.append(f"Option{len(selected) + 1}")

        options = selected + [answer_term]
        self._rng.shuffle(options)
        correct_index = options.index(answer_term)
        return options, correct_index
