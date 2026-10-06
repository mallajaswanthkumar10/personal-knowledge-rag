"""Reads .md / .txt / .pdf files out of a notes directory.

PDF support is optional - `pypdf` is only imported if a .pdf file is
actually encountered, so the rest of the pipeline works without it
installed.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from config import SUPPORTED_EXTENSIONS

log = logging.getLogger("loaders")


@dataclass
class SourceDocument:
    path: Path
    text: str
    mtime: float


def iter_source_files(notes_dir: str) -> list[Path]:
    root = Path(notes_dir)
    if not root.exists():
        return []
    return sorted(
        p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            f"skipping {path}: `pypdf` is not installed (pip install pypdf) to read PDFs"
        ) from exc

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_document(path: Path) -> SourceDocument:
    if path.suffix.lower() == ".pdf":
        text = _read_pdf(path)
    else:
        text = path.read_text(encoding="utf-8", errors="replace")

    return SourceDocument(path=path, text=text, mtime=path.stat().st_mtime)


def load_documents(notes_dir: str) -> list[SourceDocument]:
    docs = []
    for path in iter_source_files(notes_dir):
        try:
            docs.append(load_document(path))
        except RuntimeError as exc:
            log.warning(str(exc))
    return docs
