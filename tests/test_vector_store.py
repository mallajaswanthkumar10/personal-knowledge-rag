from pathlib import Path

from store.vector_store import VectorStore


def _make_store(tmp_path: Path) -> VectorStore:
    return VectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")


def test_upsert_and_query_returns_relevant_chunk(tmp_path: Path):
    store = _make_store(tmp_path)
    store.upsert_chunks(
        chunk_ids=["1", "2"],
        texts=["the quick brown fox jumps over the lazy dog", "lentil soup recipe with cumin and turmeric"],
        metadatas=[{"source": "animals.md", "chunk_index": 0}, {"source": "recipe.md", "chunk_index": 0}],
    )

    results = store.query("what spices go in the soup", top_k=1)
    assert len(results) == 1
    assert results[0].source == "recipe.md"


def test_query_on_empty_store_returns_no_results(tmp_path: Path):
    store = _make_store(tmp_path)
    assert store.query("anything", top_k=5) == []


def test_count_reflects_upserted_chunks(tmp_path: Path):
    store = _make_store(tmp_path)
    assert store.count() == 0
    store.upsert_chunks(["1"], ["some text"], [{"source": "a.md", "chunk_index": 0}])
    assert store.count() == 1


def test_delete_by_source_removes_only_matching_chunks(tmp_path: Path):
    store = _make_store(tmp_path)
    store.upsert_chunks(
        chunk_ids=["a::0", "b::0"],
        texts=["from file a", "from file b"],
        metadatas=[{"source": "a.md", "chunk_index": 0}, {"source": "b.md", "chunk_index": 0}],
    )
    store.delete_by_source("a.md")
    assert store.count() == 1
