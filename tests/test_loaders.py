from pathlib import Path

from ingest.loaders import iter_source_files, load_document, load_documents


def test_iter_source_files_finds_supported_extensions(tmp_path: Path):
    (tmp_path / "a.md").write_text("markdown note")
    (tmp_path / "b.txt").write_text("plain text note")
    (tmp_path / "c.jpg").write_bytes(b"not a document")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "d.md").write_text("nested note")

    found = {p.name for p in iter_source_files(str(tmp_path))}
    assert found == {"a.md", "b.txt", "d.md"}


def test_iter_source_files_on_missing_dir_returns_empty():
    assert iter_source_files("/path/does/not/exist") == []


def test_load_document_reads_text_content(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("hello from a note", encoding="utf-8")

    doc = load_document(path)
    assert doc.text == "hello from a note"
    assert doc.path == path
    assert doc.mtime > 0


def test_load_documents_returns_one_per_file(tmp_path: Path):
    (tmp_path / "a.md").write_text("note a")
    (tmp_path / "b.txt").write_text("note b")

    docs = load_documents(str(tmp_path))
    assert {d.text for d in docs} == {"note a", "note b"}
