# Contributing

Thanks for taking a look at this project. It started as a personal demo,
but issues and pull requests are genuinely welcome.

## Getting set up

```bash
git clone https://github.com/mallajaswanthkumar10/personal-knowledge-rag.git
cd personal-knowledge-rag
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
make install
```

Ingestion, indexing, and stats all work offline with no API key (they use
a local ONNX embedding model via Chroma). Only `ask` and `digest` need an
`ANTHROPIC_API_KEY` in `.env` - see `.env.example`.

## Before opening a PR

- Tests: `make test` (or `pytest tests/ -v`) - these don't need an API key
- Lint: `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
- Both run in CI on every push/PR, so a green run there confirms you're
  good to go.

## What's especially welcome

- More loaders in `ingest/loaders.py` (e.g. `.docx`, `.html`)
- Chunking strategy improvements in `ingest/chunking.py`
- Better source-attribution or ranking in `assistant/rag.py`
- Doc fixes in the README or `docs/ARCHITECTURE.md`

No change is too small. A draft PR is a perfectly good way to start a
conversation - you don't need to open an issue first.
