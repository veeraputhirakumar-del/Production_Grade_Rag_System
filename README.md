# Production Grade RAG System


A Production Grade Retrieval-Augmented Generation (RAG) System that enables users to upload documents, perform intelligent semantic search, and receive AI-powered answers with supporting source evidence.

The system combines FastAPI, Streamlit, ChromaDB, BM25, Sentence Transformers, and Ollama (Llama 3.2) to provide fast, accurate, and explainable responses over custom knowledge bases.

---


## Features

- Upload PDF, DOCX, TXT, CSV, and Markdown documents
- Automatic document parsing and chunking
- Embedding generation using Sentence Transformers
- ChromaDB Vector Search
- BM25 Keyword Search
- Hybrid Retrieval
- Source Evidence & Citations
- AI-powered Question Answering
- Analytics Dashboard
- Question History
- Professional Streamlit UI
- FastAPI REST API
- Local LLM using Ollama (Llama 3.2)

---

## Tech Stack

### Backend
- Python
- FastAPI
- ChromaDB
- BM25
- SQLite
- Sentence Transformers
- Ollama
- Llama 3.2

### Frontend
- Streamlit
- HTML
- CSS

---

# Project Structure

```
## Project Structure

```text
Production_Grade_RAG_System/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── config.py
│   ├── schemas.py
│   ├── chunker.py
│   ├── document_parser.py
│   ├── embedding_model.py
│   ├── chroma_store.py
│   ├── bm25_store.py
│   ├── retriever.py
│   ├── rag_pipeline.py
│   ├── llm.py
│   ├── bulk_ingestion.py
│   ├── clear_documents.py
│   ├── rag_app.db
│   ├── data/
│   │   ├── uploads/
│   │   ├── chroma_db/
│   │   └── bm25/
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   └── ANSWER_FIX.md

├── streamlit_frontend/
│   ├── app.py
│   ├── api_client.py
│   ├── styles.py
│   ├── analytics.py
│   ├── Documents.py
│   ├── requirements.txt
│   ├── .env
│   ├── .streamlit/
│   │   └── config.toml
│   ├── pages/
│      ├── 1_Chat.py
│      ├── 2_Upload.py
│      ├── 3_Documents.py
│      ├── 4_History.py
│      ├── 5_Analytics.py
│      └── 6_Settings.py
├── README.md
├── LICENSE
└── .gitignore
```
```

---

# Backend Setup

## 1. Navigate to Backend

```bash
cd backend
```

## 2. Create Virtual Environment

```bash
python -m venv venv
```

## 3. Activate Virtual Environment

### Windows (PowerShell)

```bash
venv\Scripts\Activate.ps1
```

### Windows (CMD)

```bash
venv\Scripts\activate.bat
```

### Linux / macOS

```bash
source venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Run Backend

```bash
uvicorn main:app --reload
```

Backend URL

```
http://localhost:8000
```

Swagger API

```
http://localhost:8000/docs
```

---

# Frontend Setup

## 1. Navigate to Frontend

```bash
cd frontend
```

## 2. Create Virtual Environment

```bash
python -m venv venv
```

## 3. Activate Virtual Environment

### Windows (PowerShell)

```bash
venv\Scripts\Activate.ps1
```

### Windows (CMD)

```bash
venv\Scripts\activate.bat
```

### Linux / macOS

```bash
source venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Run Frontend

```bash
streamlit run app.py
```

Frontend URL

```
http://localhost:8501
```

---

# Running the Complete System

### Step 1 — Start Ollama

```bash
ollama run llama3.2
```

### Step 2 — Start Backend

```bash
cd backend

venv\Scripts\activate

uvicorn main:app --reload
```

### Step 3 — Start Frontend

```bash
cd frontend

venv\Scripts\activate

streamlit run app.py
```

---

# Workflow

```
Upload Documents
        │
        ▼
Document Parsing
        │
        ▼
Text Chunking
        │
        ▼
Embedding Generation
        │
        ▼
ChromaDB + BM25 Indexing
        │
        ▼
Hybrid Retrieval
        │
        ▼
Llama 3.2
        │
        ▼
AI Response with Source Evidence
```

---

# Future Enhancements

- Multi-user Authentication
- Conversation Memory
- Reranking
- Agentic RAG
- Multi-Modal Document Support
- Cloud Deployment
- Feedback Learning
- Enterprise Knowledge Base

---

## License

This project is developed for educational and research purposes.
