import os

import streamlit as st

from api_client import API_URL, check_backend_health, get_documents, get_question_history
from analytics import document_stats, history_stats
from styles import (
    apply_custom_css,
    dashboard_index_health,
    dashboard_pipeline,
    dashboard_recent_documents,
    dashboard_recent_questions,
    empty_state,
    metric_card,
    page_header,
)


st.set_page_config(
    page_title="Production Grade RAG System",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css()


def dashboard_page(backend_status, backend_message, documents_result, history_result):
    page_header(
        "OVERVIEW",
        "Dashboard",
        "A summary of your document index, retrieval pipeline, and recent activity.",
        ["Hybrid Search", "ChromaDB", "BM25", "Ollama"],
    )

    documents = documents_result.get("data", [])
    history = history_result.get("data", [])

    doc_stats = document_stats(documents)
    q_stats = history_stats(history)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Documents", doc_stats["total"], "Files stored in backend")
    with col2:
        metric_card("Processed", doc_stats["processed"], "Ready for retrieval")
    with col3:
        metric_card("Total Chunks", doc_stats["total_chunks"], "Searchable text segments")
    with col4:
        metric_card("Questions Asked", q_stats["total"], "Logged in history")

    st.markdown('<div class="dashboard-section-gap"></div>', unsafe_allow_html=True)
    dashboard_pipeline()

    st.markdown('<div class="dashboard-section-gap"></div>', unsafe_allow_html=True)
    if not documents_result.get("success"):
        st.error("Could not load documents from the backend.")
        st.code(documents_result.get("error", "Unknown error"))
    elif not documents:
        empty_state(
            "No documents yet",
            "Upload a file from the Upload page to start building your knowledge base.",
            "○",
        )
    else:
        dashboard_recent_documents(documents[:5])

    st.markdown('<div class="dashboard-section-gap"></div>', unsafe_allow_html=True)
    if not history_result.get("success"):
        st.error("Could not load question history.")
        st.code(history_result.get("error", "Unknown error"))
    elif not history:
        empty_state("No questions yet", "Ask something from the Chat page to see activity here.", "○")
    else:
        dashboard_recent_questions(history[:4])

    st.markdown('<div class="dashboard-section-gap"></div>', unsafe_allow_html=True)
    newest_document = documents[0].get("created_at") if documents else None
    embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "768"))
    dashboard_index_health(
        healthy=backend_status,
        vector_count=doc_stats["total_chunks"],
        embedding_dimension=embedding_dimension,
        last_reindex=newest_document,
        api_docs_url=f"{API_URL}/docs",
        offline_message=backend_message,
    )


backend_status, backend_message = check_backend_health()
documents_result = get_documents()
history_result = get_question_history()
documents = documents_result.get("data", [])
history = history_result.get("data", [])

dashboard_page(backend_status, backend_message, documents_result, history_result)
