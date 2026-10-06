"""Splits document text into overlapping chunks for embedding.

A sliding character window rather than sentence/paragraph-aware splitting -
simple, deterministic, and easy to unit test exactly. The overlap exists so
a sentence that straddles a chunk boundary still appears whole in at least
one chunk, which matters for retrieval quality.
"""
from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == n:
            break
        start = end - overlap

    return chunks
