"""Command-line interface.

    python cli.py ingest            # scan NOTES_DIR, index new/changed files
    python cli.py ask "question"    # ask a question over your indexed notes
    python cli.py digest            # ingest, then write today's digest
    python cli.py stats             # show how many chunks are indexed
"""
from __future__ import annotations

import argparse
import logging

from assistant.digest import generate_digest
from assistant.rag import answer_question
from config import CHROMA_COLLECTION, CHROMA_DIR, NOTES_DIR
from ingest.pipeline import run_ingestion
from store.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def cmd_ingest(_args: argparse.Namespace) -> None:
    summary = run_ingestion()
    print(f"New files:     {len(summary.new_files)}")
    print(f"Updated files: {len(summary.updated_files)}")
    print(f"Removed files: {len(summary.removed_files)}")
    print(f"Chunks indexed: {summary.chunks_indexed}")


def cmd_ask(args: argparse.Namespace) -> None:
    result = answer_question(args.question)
    print(f"\n{result.answer}\n")
    if result.sources:
        print("Sources:")
        for source in result.sources:
            print(f"  - {source}")


def cmd_digest(_args: argparse.Namespace) -> None:
    summary = run_ingestion()
    digest = generate_digest(summary)
    if digest is None:
        print("Nothing new since the last run - no digest generated.")
    else:
        print(digest)


def cmd_stats(_args: argparse.Namespace) -> None:
    store = VectorStore(persist_dir=CHROMA_DIR, collection_name=CHROMA_COLLECTION)
    print(f"Notes directory: {NOTES_DIR}")
    print(f"Indexed chunks:  {store.count()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal knowledge assistant")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ingest", help="index new/changed notes").set_defaults(func=cmd_ingest)

    ask_parser = sub.add_parser("ask", help="ask a question over your notes")
    ask_parser.add_argument("question")
    ask_parser.set_defaults(func=cmd_ask)

    sub.add_parser("digest", help="ingest and generate today's digest").set_defaults(func=cmd_digest)
    sub.add_parser("stats", help="show index stats").set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
