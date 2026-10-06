"""Central config. Every setting overridable via env vars / .env."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str) -> str:
    return os.environ.get(name, default)


ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = _get("ANTHROPIC_MODEL", "claude-opus-5")

NOTES_DIR = _get("NOTES_DIR", "./data/notes")
CHROMA_DIR = _get("CHROMA_DIR", "./data/chroma")
CHROMA_COLLECTION = _get("CHROMA_COLLECTION", "personal_knowledge")
DIGEST_DIR = _get("DIGEST_DIR", "./data/digests")
MANIFEST_PATH = _get("MANIFEST_PATH", "./data/manifest.json")

CHUNK_SIZE = int(_get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(_get("CHUNK_OVERLAP", "100"))

TOP_K = int(_get("TOP_K", "5"))

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}
