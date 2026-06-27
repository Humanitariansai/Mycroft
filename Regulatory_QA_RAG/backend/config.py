from pathlib import Path
import os

# Base directory: backend/
BASE_DIR = Path(__file__).resolve().parent

# Where uploaded files will be saved
RAW_DOCS_DIR = BASE_DIR / "data" / "raw_docs"

# Where FAISS index and metadata will be saved
VECTOR_STORE_DIR = BASE_DIR / "data" / "vector_store"

# Embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Local Ollama model
OLLAMA_MODEL_NAME = "llama3.2:3b"

OLLAMA_GENERATE_URL = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434"
) + "/api/generate"

# RAG settings
CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
TOP_K = 4