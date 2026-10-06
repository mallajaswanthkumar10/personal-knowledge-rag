# Personal Knowledge Assistant

Ask questions about your own notes in plain English, and get a daily
digest of what's new - powered by a local vector search index and
Claude. Point it at a folder of markdown/text/PDF notes and it answers
only from what's actually in there, telling you when it doesn't know
rather than guessing.

This is a retrieval-augmented generation (RAG) pipeline: a genuinely
useful daily tool, and a demonstration of the data engineering skills
behind it (incremental ingestion, a vector store, cost-aware LLM calls).

## How it works

```
  your notes (data/notes/*.md, *.txt, *.pdf)
                |
                v
     incremental ingestion
  (only new/changed files are
   re-processed, tracked in a
   manifest file)
                |
                v
   split into overlapping chunks
                |
                v
   local vector index (Chroma)
                |
        -----------------
        |               |
        v               v
   ask a question   daily digest of
   -> retrieve        what changed
   relevant chunks   -> summarized
   -> Claude answers    by Claude
   grounded only in
   those chunks
```

## What's in this project

| What it does | Where to find it |
|---|---|
| Reads your notes (.md, .txt, .pdf) | `ingest/loaders.py` |
| Splits notes into chunks for indexing | `ingest/chunking.py` |
| Only re-indexes new/changed files | `ingest/pipeline.py` |
| Local vector search index | `store/vector_store.py` |
| Answers questions using Claude + your notes | `assistant/rag.py` |
| Writes a daily "what's new" summary | `assistant/digest.py` |
| Command-line interface | `cli.py` |
| Chat web UI | `app.py` |
| Optional: daily scheduling via Airflow | `orchestration/airflow_dag.py` |
| Automated tests | `tests/` |
| Deeper design notes | `docs/ARCHITECTURE.md` |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and add your Anthropic API key (get one at
https://console.anthropic.com/):

```
ANTHROPIC_API_KEY=sk-ant-...
```

Nothing else is required - the vector search runs a small local model, no
other accounts or services needed.

## Try it with the included sample notes

```bash
python cli.py ingest
python cli.py ask "What ingredients does the lentil soup need?"
```

Replace the files in `data/notes/` with your own notes, re-run `ingest`,
and ask away.

## Everyday use

```bash
# Index whatever's new or changed, then ask something
python cli.py ingest
python cli.py ask "What did I decide about the Q3 budget?"

# Get a summary of what changed since the last run
python cli.py digest

# Check how much is indexed
python cli.py stats

# Or use the chat interface instead of the CLI
streamlit run app.py
```

## Running the tests

Everything except the live Claude call is tested directly, including real
ingestion and real vector-store behavior (new/changed/deleted files, empty
queries, etc.) - no mocking required since the vector index runs locally:

```bash
pytest tests/ -v
```

## Good to know

- **Answers are grounded in your notes only.** If your notes don't cover
  a question, the assistant says it doesn't know rather than answering
  from Claude's general knowledge. That's intentional - the whole point
  is being able to trust what it tells you came from your own notes.
- **No conversation memory yet.** Each question is answered independently;
  it won't remember earlier questions in the same session.
- **Cost-conscious by default.** Answers are capped at a short length and
  use a lower reasoning effort, since this is meant to be asked questions
  many times a day. You can also switch `ANTHROPIC_MODEL` in `.env` to a
  cheaper model (see `docs/ARCHITECTURE.md` for the tradeoffs).
- **PDF support needs `pypdf`** (already in `requirements.txt`) - markdown
  and plain text work with no extra dependency.

## License

MIT — see [LICENSE](LICENSE).
