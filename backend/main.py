import os
import shutil
import threading
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from bulk_ingestion import ingest_documents_from_directory
from config import APP_NAME, BULK_DOCUMENT_DIR, EMBEDDING_MODEL, UPLOAD_DIR
from database import (
    get_chunks_for_document,
    get_document,
    get_documents,
    get_questions,
    init_db,
)
from chroma_store import chroma_store
from document_parser import SUPPORTED_EXTENSIONS
from rag_pipeline import ask_question, ingest_document
from schemas import QuestionRequest


app = FastAPI(title=APP_NAME)
bulk_ingestion_lock = threading.Lock()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(BULK_DOCUMENT_DIR, exist_ok=True)
    os.makedirs("data/chroma_db", exist_ok=True)
    os.makedirs("data/bm25", exist_ok=True)
    init_db()


@app.get("/")
def home():
    return {
        "message": "Production RAG Backend is running",
        "docs": "http://localhost:8000/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}


def process_uploaded_file(file: UploadFile):
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="No file selected")

    file_extension = os.path.splitext(filename)[1].lower()
    if file_extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}",
        )

    unique_name = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = ingest_document(file_path=file_path, filename=filename)
        if result.get("status") == "skipped":
            try:
                os.remove(file_path)
            except OSError:
                pass

        return {
            "message": (
                "Duplicate document skipped"
                if result.get("status") == "skipped"
                else "Document uploaded and processed successfully"
            ),
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/upload")
async def upload_file_for_streamlit(file: UploadFile = File(...)):
    return process_uploaded_file(file)


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    return process_uploaded_file(file)


@app.post("/documents/bulk-ingest")
def bulk_ingest_documents():
    """Ingest the configured data/documents folder synchronously."""
    if not bulk_ingestion_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="A bulk-ingestion job is already running",
        )
    try:
        return ingest_documents_from_directory(BULK_DOCUMENT_DIR)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        bulk_ingestion_lock.release()


@app.get("/documents")
def list_documents():
    return {"documents": get_documents()}


@app.get("/documents/{document_id}/details")
def document_details(document_id: int):
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = get_chunks_for_document(document_id)
    vector_details = chroma_store.get_embedding_details(
        [chunk["chroma_id"] for chunk in chunks]
    )
    enriched_chunks = []
    for chunk in chunks:
        enriched_chunks.append({
            **chunk,
            **vector_details.get(chunk["chroma_id"], {
                "embedding_dimension": 0,
                "embedding_norm": 0,
                "embedding_preview": [],
            }),
        })

    return {
        "document": document,
        "chunks": enriched_chunks,
        "vector_db": "ChromaDB",
        "embedding_model": EMBEDDING_MODEL,
    }


@app.post("/ask")
def ask(data: QuestionRequest):
    try:
        if not data.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        return ask_question(data.question)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/history")
def history_for_streamlit():
    return {"history": get_questions()}


@app.get("/questions/history")
def question_history():
    return {"questions": get_questions()}
