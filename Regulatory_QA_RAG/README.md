# RAG Document Intelligence Assistant

This project is an end-to-end Retrieval-Augmented Generation system for document question answering.

## Features

- Upload PDF and TXT documents
- Extract and preprocess document text
- Split documents into overlapping chunks
- Generate semantic embeddings using SentenceTransformers
- Store vectors in FAISS for similarity search
- Retrieve top-k relevant chunks for a user query
- Generate grounded answers using a local Ollama LLM
- Serve backend through FastAPI
- Provide frontend using Streamlit
- Docker-ready project structure

## Tech Stack

Python, FastAPI, Streamlit, FAISS, SentenceTransformers, Ollama, PyMuPDF, Docker

## Architecture

1. User uploads document
2. Text is extracted from PDF/TXT
3. Text is chunked with overlap
4. Chunks are converted into embeddings
5. Embeddings are stored in FAISS
6. User asks a question
7. Query is embedded
8. FAISS retrieves top-k similar chunks
9. Retrieved chunks are passed to the LLM
10. LLM generates grounded answer with source chunks

## Why RAG?

RAG was used instead of fine-tuning because the knowledge source is document-based and can change. Updating the document index is easier and cheaper than retraining a model.

## Why FAISS?

FAISS enables fast vector similarity search over document embeddings, reducing retrieval latency compared to brute-force vector comparison.

## How to Run

### 1. Start Ollama

```bash
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

### 2. Start Backend

```bash
cd backend
uvicorn app:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Swagger API docs:

```text
http://127.0.0.1:8000/docs
```

### 3. Start Frontend

Open a new terminal from the project root:

```bash
streamlit run frontend/streamlit_app.py
```

Frontend runs at:

```text
http://localhost:8501
```

## Evaluation

The system can be evaluated using:

- Retrieval precision@k
- Retrieval recall@k
- Answer relevance
- Groundedness
- Hallucination rate
- Latency
- User time saved

## Future Improvements

- Add authentication
- Add support for DOCX and CSV files
- Add conversation memory
- Add hybrid search using BM25 + vector search
- Add reranking for better retrieval quality
- Deploy using Docker
- Add evaluation dashboard for answer quality and latency