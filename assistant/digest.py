"""Generates a short daily digest summarizing whatever notes were newly
added or changed since the last ingestion run - the "helpful in daily
life" payoff: a morning read of what's new, instead of re-reading every
note yourself.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from assistant.claude_client import ClaudeCallError, call_claude
from config import DIGEST_DIR
from ingest.loaders import load_document
from ingest.pipeline import IngestionSummary

SYSTEM_PROMPT = """\
You write short daily digests for someone reviewing their own notes. Given
the full text of each note that's new or changed today, produce:

1. A one-paragraph overview of what's new.
2. A bulleted highlight per note, each tagged with the note's filename.

Be concise - this should be readable in under a minute.
"""


def generate_digest(summary: IngestionSummary, digest_dir: str = DIGEST_DIR) -> str | None:
    changed_paths = summary.new_files + summary.updated_files
    if not changed_paths:
        return None

    sections = []
    for path_str in changed_paths:
        path = Path(path_str)
        if not path.exists():
            continue
        doc = load_document(path)
        sections.append(f"=== {path.name} ===\n{doc.text}")

    if not sections:
        return None

    try:
        digest_text = call_claude(
            system=SYSTEM_PROMPT,
            user_content="\n\n".join(sections),
            max_tokens=1024,
            effort="low",
        )
    except ClaudeCallError as exc:
        digest_text = f"(digest generation failed: {exc})"

    out_dir = Path(digest_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date.today().isoformat()}.md"
    out_path.write_text(digest_text, encoding="utf-8")

    return digest_text
