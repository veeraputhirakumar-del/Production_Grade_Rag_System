import hashlib
import os
import time

from bm25_store import bm25_store
from chroma_store import chroma_store
from chunker import chunk_pages
from database import (
    delete_chunks_for_document,
    get_processed_document_by_hash,
    insert_chunks_bulk,
    insert_document,
    insert_question,
    insert_retrieval_log,
    update_document_status,
)
from document_parser import parse_document
from llm import generate_answer
from retriever import hybrid_search


def hash_file(file_path):
    digest = hashlib.sha256()
    with open(file_path, "rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ingest_document(file_path, filename=None, rebuild_bm25=True, file_hash=None):
    """Ingest one document through the shared upload/bulk pipeline."""
    filename = filename or os.path.basename(file_path)
    file_type = os.path.splitext(filename)[1].lower()
    file_hash = file_hash or hash_file(file_path)

    existing = get_processed_document_by_hash(file_hash)
    if existing:
        return {
            "document_id": existing["id"],
            "filename": existing["filename"],
            "total_chunks": existing.get("total_chunks", 0),
            "status": "skipped",
            "reason": "duplicate_content",
        }

    document_id = insert_document(
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        file_hash=file_hash,
    )

    try:
        pages = parse_document(file_path)
        chunks = chunk_pages(pages)
        if not chunks:
            raise ValueError("The document produced no text chunks")

        stored_chunks = insert_chunks_bulk(document_id, chunks)
        chroma_chunks = [
            {
                "chroma_id": chunk["chroma_id"],
                "text": chunk["text"],
                "metadata": {
                    "document_id": document_id,
                    "chunk_id": chunk["chunk_id"],
                    "filename": filename,
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"],
                },
            }
            for chunk in stored_chunks
        ]
        chroma_store.add_chunks(chroma_chunks)

        update_document_status(
            document_id=document_id,
            status="processed",
            total_chunks=len(chunks),
        )

        if rebuild_bm25:
            bm25_store.rebuild()

        return {
            "document_id": document_id,
            "filename": filename,
            "total_chunks": len(chunks),
            "status": "processed",
        }
    except Exception:
        try:
            chroma_store.delete_document(document_id)
        except Exception:
            pass
        delete_chunks_for_document(document_id)
        update_document_status(document_id, "failed", 0)
        if rebuild_bm25:
            try:
                bm25_store.rebuild()
            except Exception:
                pass
        raise


ANSWER_MODE_MARKER = "\n\nAnswer mode instruction:"


def split_question_and_instruction(question):
    clean_question, marker, instruction = question.partition(ANSWER_MODE_MARKER)
    return clean_question.strip(), instruction.strip() if marker else ""


def ask_question(question):
    start_time = time.time()
    clean_question, answer_instruction = split_question_and_instruction(question)
    retrieved_contexts = hybrid_search(
        query=clean_question,
        semantic_k=8,
        bm25_k=8,
        final_k=5,
    )

    if not retrieved_contexts:
        answer = "I could not find this information in the uploaded documents."
    else:
        answer = generate_answer(
            clean_question,
            retrieved_contexts,
            answer_instruction=answer_instruction,
        )

    latency_ms = int((time.time() - start_time) * 1000)
    question_id = insert_question(
        question=clean_question,
        answer=answer,
        latency_ms=latency_ms,
        status="success",
    )

    for rank, item in enumerate(retrieved_contexts, start=1):
        metadata = item.get("metadata", {})
        insert_retrieval_log(
            question_id=question_id,
            chunk_id=metadata.get("chunk_id"),
            chroma_id=item.get("chroma_id"),
            source_type=item.get("source_type", "hybrid"),
            score=item.get("final_score", item.get("score", 0)),
            rank_position=rank,
        )

    sources = []
    for item in retrieved_contexts:
        metadata = item.get("metadata", {})
        sources.append({
            "filename": metadata.get("filename"),
            "page_number": metadata.get("page_number"),
            "chunk_index": metadata.get("chunk_index"),
            "score": item.get("final_score", item.get("score", 0)),
            "text_preview": item.get("text", "")[:700],
        })

    return {
        "question_id": question_id,
        "question": clean_question,
        "answer": answer,
        "sources": sources,
        "latency_ms": latency_ms,
    }
