"""Retrieval-augmented Q&A over your own indexed notes.

Retrieves the top-k most relevant chunks from the vector store, hands them
to Claude as grounding context, and asks it to answer *only* from that
context (and say so when it can't) - the standard RAG pattern for keeping
answers tied to your actual notes instead of the model's general
knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass

from assistant.claude_client import ClaudeCallError, call_claude
from config import CHROMA_COLLECTION, CHROMA_DIR, TOP_K
from store.vector_store import RetrievedChunk, VectorStore

SYSTEM_PROMPT = """\
You are a personal knowledge assistant. You answer questions using ONLY the
provided excerpts from the user's own notes - never your general knowledge.

Rules:
- If the excerpts don't contain enough information to answer, say so plainly
  instead of guessing.
- Keep answers concise - a few sentences, not an essay.
- When you use a fact from an excerpt, mention which source it came from.
"""


@dataclass
class AnswerResult:
    answer: str
    sources: list[str]
    had_context: bool


def _build_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n---\n\n".join(f"[Source: {chunk.source}]\n{chunk.text}" for chunk in chunks)


def answer_question(question: str, top_k: int = TOP_K) -> AnswerResult:
    store = VectorStore(persist_dir=CHROMA_DIR, collection_name=CHROMA_COLLECTION)
    chunks = store.query(question, top_k=top_k)

    if not chunks:
        return AnswerResult(
            answer="I don't have any indexed notes yet - run ingestion first.",
            sources=[],
            had_context=False,
        )

    context = _build_context(chunks)
    # Grounded Q&A over a handful of short note excerpts rarely needs a long
    # answer or deep reasoning - keeping both capped controls cost on a tool
    # meant to be queried many times a day.
    try:
        answer = call_claude(
            system=SYSTEM_PROMPT,
            user_content=f"Excerpts from my notes:\n\n{context}\n\nQuestion: {question}",
            max_tokens=1024,
            effort="low",
        )
    except ClaudeCallError as exc:
        return AnswerResult(answer=str(exc), sources=[], had_context=True)

    sources = sorted({chunk.source for chunk in chunks})
    return AnswerResult(answer=answer, sources=sources, had_context=True)
