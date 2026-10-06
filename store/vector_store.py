"""Thin wrapper around a local, persistent Chroma vector database.

Uses Chroma's built-in default embedding function (a small ONNX MiniLM
model that runs locally, no API key and no torch/GPU needed) rather than
calling out to an embeddings API - keeps the whole pipeline runnable
offline aside from the actual Claude Q&A call.
"""
from __future__ import annotations

from dataclasses import dataclass

import chromadb


@dataclass
class RetrievedChunk:
    text: str
    source: str
    chunk_index: int
    distance: float


class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str) -> None:
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(collection_name)

    def upsert_chunks(self, chunk_ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
        if not chunk_ids:
            return
        self._collection.upsert(ids=chunk_ids, documents=texts, metadatas=metadatas)

    def delete_by_source(self, source: str) -> None:
        self._collection.delete(where={"source": source})

    def query(self, question: str, top_k: int) -> list[RetrievedChunk]:
        if self._collection.count() == 0:
            return []
        result = self._collection.query(query_texts=[question], n_results=min(top_k, self._collection.count()))

        chunks = []
        docs = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]
        for text, meta, distance in zip(docs, metadatas, distances):
            chunks.append(
                RetrievedChunk(
                    text=text,
                    source=meta.get("source", "unknown"),
                    chunk_index=meta.get("chunk_index", 0),
                    distance=distance,
                )
            )
        return chunks

    def count(self) -> int:
        return self._collection.count()
