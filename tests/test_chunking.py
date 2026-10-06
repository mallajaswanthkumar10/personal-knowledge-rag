import pytest

from ingest.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_text_shorter_than_chunk_size_is_one_chunk():
    assert chunk_text("hello world", chunk_size=800, overlap=100) == ["hello world"]


def test_text_longer_than_chunk_size_splits_into_multiple_chunks():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 400 for c in chunks)


def test_chunks_overlap_by_the_requested_amount():
    text = "0123456789" * 50  # 500 chars
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    # the end of one chunk should reappear at the start of the next
    for prev, nxt in zip(chunks, chunks[1:]):
        assert prev[-20:] == nxt[:20]


def test_full_text_is_covered_with_no_gaps():
    text = "x" * 250
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    # reconstruct by removing the known overlap and check nothing was skipped
    rebuilt = chunks[0]
    for chunk in chunks[1:]:
        rebuilt += chunk[20:]
    assert rebuilt == text


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=100, overlap=100)
