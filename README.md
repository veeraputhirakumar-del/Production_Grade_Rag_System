
# Production Grade RAG System

A document-based AI knowledge assistant built using Retrieval-Augmented Generation (RAG). Users can upload PDF, DOCX, TXT, CSV, and Markdown files and ask natural-language questions about their content.

The system processes documents through text extraction, chunking, embedding generation, and indexing. It combines ChromaDB vector search with BM25 keyword search to retrieve relevant information. Llama 3.2 then generates an answer using the retrieved context and displays supporting source evidence.

## Key Features

- Multiple document format support
- Automatic chunking and embedding
- ChromaDB vector search
- BM25 keyword retrieval
- Hybrid search and reranking
- Source evidence for answers
- Question history and analytics
- FastAPI backend
- Professional Streamlit interface
- Local LLM support through Ollama

## Technology Stack

- Python
- FastAPI
- Streamlit
- Ollama and Llama 3.2
- ChromaDB
- BM25
- Sentence Transformers
- SQLite
