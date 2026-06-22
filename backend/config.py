import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _path_from_env(name, default):
    value = Path(os.getenv(name, default)).expanduser()
    if not value.is_absolute():
        value = BASE_DIR / value
    return str(value.resolve())

APP_NAME = os.getenv("APP_NAME", "Production RAG System")

UPLOAD_DIR = _path_from_env("UPLOAD_DIR", "data/uploads")
BULK_DOCUMENT_DIR = _path_from_env(
    "BULK_DOCUMENT_DIR",
    "../streamlit_frontend/data/documents",
)
CHROMA_DIR = _path_from_env("CHROMA_DIR", "data/chroma_db")
BM25_DIR = _path_from_env("BM25_DIR", "data/bm25")

SQLITE_DB_PATH = _path_from_env("SQLITE_DB_PATH", "rag_app.db")

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
CHROMA_BATCH_SIZE = int(os.getenv("CHROMA_BATCH_SIZE", "128"))

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
