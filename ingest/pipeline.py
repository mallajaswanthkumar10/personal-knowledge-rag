"""Incremental ingestion: scans the notes directory, (re)indexes only files
that are new or changed since the last run, and removes anything that was
deleted from disk - a manifest file (path -> last-seen mtime) is the only
state needed, so re-running is cheap and idempotent.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from config import CHROMA_COLLECTION, CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE, MANIFEST_PATH, NOTES_DIR
from ingest.chunking import chunk_text
from ingest.loaders import load_documents
from store.vector_store import VectorStore

log = logging.getLogger("pipeline")


@dataclass
class IngestionSummary:
    new_files: list[str] = field(default_factory=list)
    updated_files: list[str] = field(default_factory=list)
    removed_files: list[str] = field(default_factory=list)
    chunks_indexed: int = 0


def _load_manifest(path: str) -> dict[str, float]:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _save_manifest(path: str, manifest: dict[str, float]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run_ingestion(
    notes_dir: str = NOTES_DIR,
    chroma_dir: str = CHROMA_DIR,
    collection: str = CHROMA_COLLECTION,
    manifest_path: str = MANIFEST_PATH,
) -> IngestionSummary:
    manifest = _load_manifest(manifest_path)
    new_manifest = dict(manifest)
    summary = IngestionSummary()

    store = VectorStore(persist_dir=chroma_dir, collection_name=collection)
    docs = load_documents(notes_dir)
    seen_keys = set()

    for doc in docs:
        key = str(doc.path)
        seen_keys.add(key)

        if manifest.get(key) == doc.mtime:
            continue  # unchanged - skip re-embedding

        is_update = key in manifest
        if is_update:
            store.delete_by_source(key)

        chunks = chunk_text(doc.text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        ids = [f"{key}::{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": key,
                "chunk_index": i,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(len(chunks))
        ]
        store.upsert_chunks(ids, chunks, metadatas)

        new_manifest[key] = doc.mtime
        summary.chunks_indexed += len(chunks)
        (summary.updated_files if is_update else summary.new_files).append(key)

    removed_keys = set(manifest) - seen_keys
    for key in removed_keys:
        store.delete_by_source(key)
        del new_manifest[key]
        summary.removed_files.append(key)

    _save_manifest(manifest_path, new_manifest)
    log.info(
        "ingestion complete: %d new, %d updated, %d removed, %d chunks indexed",
        len(summary.new_files),
        len(summary.updated_files),
        len(summary.removed_files),
        summary.chunks_indexed,
    )
    return summary
