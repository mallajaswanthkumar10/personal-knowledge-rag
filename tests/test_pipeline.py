import os
from pathlib import Path

from ingest.pipeline import run_ingestion
from store.vector_store import VectorStore


def _run(tmp_path: Path, notes_dir: Path):
    return run_ingestion(
        notes_dir=str(notes_dir),
        chroma_dir=str(tmp_path / "chroma"),
        collection="test",
        manifest_path=str(tmp_path / "manifest.json"),
    )


def test_first_run_indexes_all_files(tmp_path: Path):
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "a.md").write_text("note a content")
    (notes_dir / "b.md").write_text("note b content")

    summary = _run(tmp_path, notes_dir)

    assert len(summary.new_files) == 2
    assert summary.updated_files == []
    assert summary.chunks_indexed == 2


def test_second_run_with_no_changes_skips_everything(tmp_path: Path):
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "a.md").write_text("note a content")
    _run(tmp_path, notes_dir)

    summary = _run(tmp_path, notes_dir)

    assert summary.new_files == []
    assert summary.updated_files == []
    assert summary.chunks_indexed == 0


def test_modified_file_is_reindexed(tmp_path: Path):
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    note_path = notes_dir / "a.md"
    note_path.write_text("original content")
    _run(tmp_path, notes_dir)

    note_path.write_text("changed content")
    os.utime(note_path, None)  # bump mtime in case the write was too fast to change it
    newer = note_path.stat().st_mtime + 1
    os.utime(note_path, (newer, newer))

    summary = _run(tmp_path, notes_dir)

    assert summary.new_files == []
    assert summary.updated_files == [str(note_path)]
    assert summary.chunks_indexed == 1


def test_deleted_file_is_removed_from_index(tmp_path: Path):
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    note_path = notes_dir / "a.md"
    note_path.write_text("note a content")
    _run(tmp_path, notes_dir)

    note_path.unlink()
    summary = _run(tmp_path, notes_dir)

    assert summary.removed_files == [str(note_path)]
    store = VectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    assert store.count() == 0
