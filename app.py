"""Streamlit chat UI for the personal knowledge assistant.

Run:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from assistant.rag import answer_question
from config import CHROMA_COLLECTION, CHROMA_DIR, NOTES_DIR
from ingest.pipeline import run_ingestion
from store.vector_store import VectorStore

st.set_page_config(page_title="Personal Knowledge Assistant", layout="centered")
st.title("Ask your notes")
st.caption(f"Answers are grounded only in files under `{NOTES_DIR}`.")

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.subheader("Index")
    store = VectorStore(persist_dir=CHROMA_DIR, collection_name=CHROMA_COLLECTION)
    st.metric("Indexed chunks", store.count())

    if st.button("Re-index notes now"):
        with st.spinner("Scanning for new/changed notes..."):
            summary = run_ingestion()
        st.success(
            f"{len(summary.new_files)} new, {len(summary.updated_files)} updated, "
            f"{len(summary.removed_files)} removed, {summary.chunks_indexed} chunks indexed"
        )
        st.rerun()

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.write(turn["content"])
        if turn.get("sources"):
            st.caption("Sources: " + ", ".join(turn["sources"]))

question = st.chat_input("Ask something about your notes...")
if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = answer_question(question)
        st.write(result.answer)
        if result.sources:
            st.caption("Sources: " + ", ".join(result.sources))

    st.session_state.history.append(
        {"role": "assistant", "content": result.answer, "sources": result.sources}
    )
