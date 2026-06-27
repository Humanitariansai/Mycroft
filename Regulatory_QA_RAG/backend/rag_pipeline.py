import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple

import faiss
import fitz  # PyMuPDF
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

from config import (
    RAW_DOCS_DIR,
    VECTOR_STORE_DIR,
    EMBEDDING_MODEL_NAME,
    OLLAMA_MODEL_NAME,
    OLLAMA_GENERATE_URL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
)


class RAGPipeline:
    def __init__(self):
        """
        Initialize embedding model and paths.
        """
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.index_path = VECTOR_STORE_DIR / "faiss.index"
        self.metadata_path = VECTOR_STORE_DIR / "metadata.pkl"

        RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

    def extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF using PyMuPDF.
        """
        text = ""

        with fitz.open(file_path) as doc:
            for page_number, page in enumerate(doc, start=1):
                page_text = page.get_text()
                text += f"\n\n[Page {page_number}]\n{page_text}"

        return text

    def extract_text_from_txt(self, file_path: Path) -> str:
        """
        Extract text from a .txt file.
        """
        return file_path.read_text(encoding="utf-8", errors="ignore")

    def load_documents(self) -> List[Dict]:
        """
        Load all PDF and TXT files from raw_docs folder.
        """
        documents = []

        for file_path in RAW_DOCS_DIR.iterdir():
            if file_path.suffix.lower() == ".pdf":
                text = self.extract_text_from_pdf(file_path)
            elif file_path.suffix.lower() == ".txt":
                text = self.extract_text_from_txt(file_path)
            else:
                continue

            documents.append(
                {
                    "file_name": file_path.name,
                    "text": text,
                }
            )

        return documents

    def chunk_text(self, text: str, file_name: str) -> List[Dict]:
        """
        Split long document text into overlapping chunks.
        """
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "file_name": file_name,
                        "text": chunk_text,
                    }
                )

            chunk_id += 1
            start += CHUNK_SIZE - CHUNK_OVERLAP

        return chunks

    def build_vector_store(self) -> Dict:
        """
        Create FAISS vector index from all documents.
        """
        documents = self.load_documents()

        if not documents:
            return {
                "status": "error",
                "message": "No PDF or TXT documents found in raw_docs folder.",
            }

        all_chunks = []

        for doc in documents:
            chunks = self.chunk_text(doc["text"], doc["file_name"])
            all_chunks.extend(chunks)

        if not all_chunks:
            return {
                "status": "error",
                "message": "Documents loaded, but no text chunks were created.",
            }

        texts = [chunk["text"] for chunk in all_chunks]

        # Generate embeddings
        embeddings = self.embedding_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        # Convert to float32 because FAISS expects float32 vectors
        embeddings = np.array(embeddings).astype("float32")

        # Normalize embeddings for cosine similarity using inner product
        faiss.normalize_L2(embeddings)

        embedding_dim = embeddings.shape[1]

        # IndexFlatIP = inner product search
        index = faiss.IndexFlatIP(embedding_dim)
        index.add(embeddings)

        # Save FAISS index
        faiss.write_index(index, str(self.index_path))

        # Save chunk metadata
        with open(self.metadata_path, "wb") as f:
            pickle.dump(all_chunks, f)

        return {
            "status": "success",
            "message": "Vector store built successfully.",
            "documents_loaded": len(documents),
            "chunks_created": len(all_chunks),
            "embedding_dimension": embedding_dim,
        }

    def load_vector_store(self) -> Tuple[faiss.Index, List[Dict]]:
        """
        Load FAISS index and chunk metadata.
        """
        if not self.index_path.exists() or not self.metadata_path.exists():
            raise FileNotFoundError(
                "Vector store not found. Please upload documents and build the index first."
            )

        index = faiss.read_index(str(self.index_path))

        with open(self.metadata_path, "rb") as f:
            metadata = pickle.load(f)

        return index, metadata

    def retrieve_context(self, query: str, top_k: int = TOP_K) -> List[Dict]:
        """
        Retrieve top-k most relevant chunks for the query.
        """
        index, metadata = self.load_vector_store()

        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True,
        ).astype("float32")

        faiss.normalize_L2(query_embedding)

        scores, indices = index.search(query_embedding, top_k)

        retrieved_chunks = []

        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue

            chunk = metadata[idx].copy()
            chunk["similarity_score"] = float(score)
            retrieved_chunks.append(chunk)

        return retrieved_chunks

    def build_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """
        Build final prompt for the LLM using retrieved document chunks.
        """
        context_blocks = []

        for i, chunk in enumerate(retrieved_chunks, start=1):
            context_blocks.append(
                f"Source {i}: {chunk['file_name']} | Chunk {chunk['chunk_id']}\n"
                f"{chunk['text']}"
            )

        context = "\n\n".join(context_blocks)

        prompt = f"""
You are a careful document question-answering assistant.

Answer the user's question using ONLY the context below.

Rules:
1. If the answer is not present in the context, say: "I do not have enough information in the uploaded documents."
2. Do not make up facts.
3. Keep the answer clear and structured.
4. At the end, mention which sources/chunks were used.

Context:
{context}

User question:
{query}

Answer:
"""
        return prompt

    def generate_answer(self, prompt: str) -> str:
        """
        Generate answer using local Ollama model.
        """
        payload = {
            "model": OLLAMA_MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(
                OLLAMA_GENERATE_URL,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            return (
                "Could not connect to Ollama. Make sure Ollama is installed and running. "
                "Try running: ollama run llama3.2:3b"
            )

        except requests.exceptions.Timeout:
            return "The LLM request timed out. Try a shorter question or fewer retrieved chunks."

        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def answer_question(self, query: str) -> Dict:
        """
        Complete RAG flow:
        query -> retrieve chunks -> build prompt -> generate answer
        """
        retrieved_chunks = self.retrieve_context(query)

        if not retrieved_chunks:
            return {
                "answer": "No relevant context found.",
                "sources": [],
            }

        prompt = self.build_prompt(query, retrieved_chunks)
        answer = self.generate_answer(prompt)

        sources = [
            {
                "file_name": chunk["file_name"],
                "chunk_id": chunk["chunk_id"],
                "similarity_score": round(chunk["similarity_score"], 4),
                "preview": chunk["text"][:300],
            }
            for chunk in retrieved_chunks
        ]

        return {
            "answer": answer,
            "sources": sources,
        }