# Architecture Notes

## Data flow

```
data/notes/*.{md,txt,pdf}
        |
        v
  ingest/loaders.py      -- reads each file's text + mtime
        |
        v
  ingest/pipeline.py      -- compares mtime against data/manifest.json;
                              only new/changed files proceed
        |
        v
  ingest/chunking.py       -- splits each file into overlapping chunks
        |
        v
  store/vector_store.py    -- embeds + upserts chunks into local Chroma
        |
        v
  data/chroma/ (persisted vector index)
        |
        v
  assistant/rag.py          -- embeds the question, retrieves top-k chunks,
                                 sends them + the question to Claude
        |
        v
  cli.py "ask" / app.py chat UI
```

`assistant/digest.py` reuses the same ingestion summary to summarize
*only what changed today* into a short digest - it doesn't re-read your
whole notes folder every time.

## Why incremental ingestion, not full re-index every time

Re-embedding every note on every run wastes compute and, if you ever swap
the local embedding model for a paid embeddings API, money. `ingest/pipeline.py`
keeps a manifest (`data/manifest.json`) mapping file path -> last-seen
modification time. On each run:

- **Unchanged file** (mtime matches manifest): skipped entirely.
- **New or modified file**: re-chunked and re-embedded; if it was
  previously indexed, its old chunks are deleted first (by a `source`
  metadata filter) so stale content doesn't linger alongside the new
  version.
- **Deleted file** (in the manifest but no longer on disk): its chunks are
  removed from the index and it drops out of the manifest.

This is the same incremental-sync pattern used in real CDC pipelines, just
keyed on filesystem mtime instead of a database's change log.

## Why local embeddings instead of an embeddings API

Chroma's default embedding function runs a small ONNX MiniLM model
locally (no GPU, no API key, ~80MB download cached after first use). For a
personal notes corpus (hundreds to low thousands of chunks), this is
"good enough" semantic search without adding a second paid API dependency
or a network round-trip to every ingestion run. If you outgrow it -
much larger corpora, multilingual notes, higher retrieval precision -
swap `store/vector_store.py` to call a dedicated embeddings API (e.g.
Voyage AI, which Anthropic recommends) instead; the rest of the pipeline
doesn't need to change.

## Why retrieval-augmented generation instead of just asking Claude

Without retrieval, Claude would answer from its general training
knowledge - not from *your* notes, and it has no way to know about
anything you wrote yesterday. RAG grounds every answer in actual excerpts
retrieved from your own index, and the system prompt explicitly instructs
Claude to say "I don't know" rather than guess when the excerpts don't
cover the question - the whole point of a personal knowledge tool is that
you can trust what it tells you came from your own notes.

## Cost awareness

This is meant to be queried many times a day, so `assistant/rag.py` and
`assistant/digest.py` deliberately:

- Cap `max_tokens` at 1024 - grounded answers over a few short note
  excerpts don't need long responses.
- Use `effort: "low"` - retrieval Q&A over short context is not a hard
  reasoning task; low effort is faster and cheaper with no meaningful
  quality loss for this workload.
- Default to `claude-opus-5`, but `ANTHROPIC_MODEL` in `.env` can be set to
  `claude-sonnet-5` or `claude-haiku-4-5` for a frequently-queried personal
  tool where the cheaper models are usually plenty - that's a tradeoff
  only you can make for your own usage pattern, so it's a config knob, not
  a silent default downgrade.

## Scaling this up

- **More sources**: add a loader for `.eml` (exported emails) or a Gmail/
  IMAP connector in `ingest/loaders.py` - the rest of the pipeline (chunk,
  embed, index) doesn't change.
- **Production scheduling**: `orchestration/airflow_dag.py` shows the same
  `run_ingestion()` / `generate_digest()` functions wired into a daily
  Airflow DAG instead of being run by hand via `cli.py`.
- **Conversation memory**: today each `ask` is independent (no chat
  history is sent to Claude). Multi-turn follow-ups ("what about last
  week?") would need the chat history included in the request - left out
  here to keep the RAG grounding logic easy to reason about.
