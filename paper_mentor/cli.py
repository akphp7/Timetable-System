from __future__ import annotations

import argparse
from pathlib import Path

from .config import ChunkingConfig, EngineConfig
from .engine import PaperMentorEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PaperMentor: adaptive research-paper learning engine"
    )
    parser.add_argument(
        "--pdfs",
        nargs="+",
        required=True,
        help="One or more PDF files to ingest",
    )
    parser.add_argument(
        "--strategy",
        default="overlap",
        choices=["fixed", "overlap", "semantic"],
        help="Default chunking strategy for interactive mode",
    )
    parser.add_argument("--top-k", type=int, default=4, help="Top-K retrieval size")
    parser.add_argument(
        "--question",
        help="If provided, run one question and exit instead of interactive mode",
    )
    return parser


def run_single_question(engine: PaperMentorEngine, question: str, strategy: str) -> None:
    answer = engine.ask(question, strategy=strategy)
    print("\nAnswer:\n")
    print(answer.answer)
    if answer.citations:
        print("\nCitations:")
        for citation in answer.citations:
            print(
                f"- {citation.source_path} | chunk={citation.chunk_id} | score={citation.score:.4f}"
            )


def run_quiz(engine: PaperMentorEngine, topic: str, strategy: str) -> None:
    questions = engine.create_quiz(topic=topic, strategy=strategy, num_questions=5)
    if not questions:
        print("No quiz could be generated for this topic.")
        return

    user_answers: list[int] = []
    print(f"\nQuiz on: {topic}\n")

    for index, question in enumerate(questions, start=1):
        print(f"Q{index}. {question.prompt}")
        for option_idx, option in enumerate(question.options, start=1):
            print(f"   {option_idx}. {option}")

        raw = input("Your choice (1-4): ").strip()
        try:
            selected = max(1, min(4, int(raw))) - 1
        except ValueError:
            selected = -1
        user_answers.append(selected)

    result = engine.submit_quiz(topic=topic, questions=questions, user_answers=user_answers)
    print(
        f"\nScore: {result.score}/{result.total} "
        f"(accuracy={result.accuracy * 100:.1f}%)"
    )


def run_interactive(engine: PaperMentorEngine, strategy: str) -> None:
    print("\nInteractive mode commands:")
    print("  ask <question>")
    print("  flashcards <topic>")
    print("  quiz <topic>")
    print("  mastery <topic>")
    print("  strategies")
    print("  exit")

    while True:
        raw = input("\npapermentor> ").strip()
        if not raw:
            continue
        if raw.lower() in {"exit", "quit"}:
            break

        if raw.startswith("ask "):
            question = raw[4:].strip()
            if not question:
                print("Please provide a question after 'ask'.")
                continue
            run_single_question(engine, question, strategy)
            continue

        if raw.startswith("flashcards "):
            topic = raw[len("flashcards ") :].strip()
            cards = engine.make_flashcards(topic=topic, strategy=strategy, count=5)
            if not cards:
                print("No flashcards generated.")
                continue
            for idx, card in enumerate(cards, start=1):
                print(f"\nCard {idx}: {card.prompt}")
                print(f"Answer: {card.answer}")
            continue

        if raw.startswith("quiz "):
            topic = raw[len("quiz ") :].strip()
            run_quiz(engine, topic=topic, strategy=strategy)
            continue

        if raw.startswith("mastery "):
            topic = raw[len("mastery ") :].strip()
            mastery = engine.assessment_agent.get_mastery(topic)
            print(f"Mastery for '{topic}': {mastery:.3f}")
            continue

        if raw == "strategies":
            print("Available:", ", ".join(engine.available_strategies()))
            continue

        print("Unknown command.")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    missing = [path for path in args.pdfs if not Path(path).exists()]
    if missing:
        raise FileNotFoundError(f"Missing PDF files: {missing}")

    engine = PaperMentorEngine(
        engine_config=EngineConfig(top_k=max(1, args.top_k)),
        chunking_config=ChunkingConfig(),
    )

    stats = engine.ingest_pdfs(args.pdfs)
    print("Ingestion complete. Chunks by strategy:")
    for strategy, count in stats.items():
        print(f"- {strategy}: {count}")

    if args.question:
        run_single_question(engine, args.question, args.strategy)
        return

    run_interactive(engine, args.strategy)


if __name__ == "__main__":
    main()
