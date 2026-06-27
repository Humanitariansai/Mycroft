from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import RAW_DOCS_DIR
from rag_pipeline import RAGPipeline


app = FastAPI(
    title="RAG Document Intelligence API",
    description="Upload documents, build FAISS vector store, and ask RAG-based questions.",
    version="1.0.0",
)

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = RAGPipeline()


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "RAG Document Intelligence API is running.",
        "docs": "Visit /docs for Swagger UI.",
    }


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    saved_files = []

    for file in files:
        suffix = Path(file.filename).suffix.lower()

        if suffix not in [".pdf", ".txt"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.filename}. Only PDF and TXT are allowed.",
            )

        file_path = RAW_DOCS_DIR / file.filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        saved_files.append(file.filename)

    return {
        "status": "success",
        "message": "Files uploaded successfully.",
        "files": saved_files,
    }
    
@app.post("/build-index")
def build_index():
    """
    Build FAISS vector index from uploaded documents.
    """
    result = rag.build_vector_store()

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@app.post("/ask")
def ask_question(request: QuestionRequest):
    """
    Ask a question over uploaded documents.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = rag.answer_question(request.question)
        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/documents")
def list_documents():
    """
    List uploaded documents.
    """
    files = []

    for file_path in RAW_DOCS_DIR.iterdir():
        if file_path.suffix.lower() in [".pdf", ".txt"]:
            files.append(file_path.name)

    return {
        "documents": files,
        "count": len(files),
    }