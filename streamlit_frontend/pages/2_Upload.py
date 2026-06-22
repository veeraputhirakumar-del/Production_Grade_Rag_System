import html
import os

import streamlit as st

from api_client import upload_document
from styles import (
    apply_custom_css,
    upload_processing_timeline,
    upload_success_panel,
)


st.set_page_config(
    page_title="Upload · Production Grade RAG System",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css()


SUPPORTED_TYPES = ["txt", "pdf", "docx", "csv", "md"]
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))


def init_upload_state():
    defaults = {
        "upload_in_progress": False,
        "upload_started": False,
        "upload_result": None,
        "upload_error": None,
        "upload_filename": None,
        "upload_size_bytes": 0,
        "upload_steps": ["queued"] * 5,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def format_file_size(size_bytes):
    size = float(size_bytes or 0)
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / 1024:.0f} KB"


def normalize_upload_data(result):
    payload = result.get("data") or {}
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload if isinstance(payload, dict) else {}


def reset_for_file(uploaded_file):
    signature = f"{uploaded_file.name}:{uploaded_file.size}"
    if st.session_state.upload_filename == signature:
        return
    st.session_state.upload_filename = signature
    st.session_state.upload_size_bytes = uploaded_file.size
    st.session_state.upload_result = None
    st.session_state.upload_error = None
    st.session_state.upload_started = False
    st.session_state.upload_steps = ["queued"] * 5


def timeline_details(uploaded_file, data=None):
    data = data or {}
    total_chunks = data.get("total_chunks") or data.get("chunks_created")
    pages = data.get("total_pages") or data.get("pages")
    tokens = data.get("total_tokens") or data.get("tokens")

    extracted = "Text extraction pending"
    if st.session_state.upload_steps[1] == "complete":
        if pages and tokens:
            extracted = f"{pages} pages · {int(tokens):,} tokens"
        elif pages:
            extracted = f"{pages} pages extracted"
        else:
            extracted = "Document text extracted"

    chunks = "Waiting for extracted text"
    if st.session_state.upload_steps[2] == "complete":
        chunks = (
            f"{total_chunks} chunks · {CHUNK_SIZE}-token window"
            if total_chunks is not None
            else f"Chunks created · {CHUNK_SIZE}-token window"
        )

    return [
        ("File uploaded", f"{uploaded_file.name} · {format_file_size(uploaded_file.size)}"),
        ("Text extracted", extracted),
        ("Chunks created", chunks),
        ("Stored in vector database", f"ChromaDB · {EMBEDDING_DIMENSION}-dim embeddings"),
        ("BM25 index rebuilt", "Hybrid retrieval ready"),
    ]


init_upload_state()

st.markdown(
    """
    <div class="upload-page-header">
        <h1>Upload Knowledge</h1>
        <p>Add TXT, PDF, DOCX, CSV, or MD files. The backend parses, chunks, embeds, and indexes the content automatically.</p>
        <div class="upload-capability-row">
            <span>Text Extraction</span>
            <span>Chunking</span>
            <span>Vector Store</span>
            <span>BM25 Rebuild</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="compact-upload-label">Drop a file here, or click to browse</div>',
    unsafe_allow_html=True,
)
with st.container(key="compact_upload"):
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=SUPPORTED_TYPES,
        label_visibility="collapsed",
        key="knowledge_file",
    )

if uploaded_file:
    reset_for_file(uploaded_file)

    with st.container(key="selected_upload"):
        file_col, action_col = st.columns([0.76, 0.24], vertical_alignment="center")
        with file_col:
            st.markdown(
                f"""
                <div class="selected-file-name">{html.escape(uploaded_file.name)}</div>
                <div class="selected-file-meta">{format_file_size(uploaded_file.size)} · Ready to process</div>
                """,
                unsafe_allow_html=True,
            )
        with action_col:
            if st.button(
                "Upload and process",
                type="primary",
                width="stretch",
                disabled=st.session_state.upload_in_progress,
            ):
                st.session_state.upload_in_progress = True
                st.session_state.upload_started = True
                st.session_state.upload_result = None
                st.session_state.upload_error = None
                st.session_state.upload_steps = ["complete", "running", "queued", "queued", "queued"]

    if st.session_state.upload_started:
        upload_data = normalize_upload_data(st.session_state.upload_result or {})
        upload_processing_timeline(
            steps=timeline_details(uploaded_file, upload_data),
            states=st.session_state.upload_steps,
            overall_status=(
                "In progress"
                if st.session_state.upload_in_progress
                else "Completed"
                if st.session_state.upload_result
                else "Failed"
                if st.session_state.upload_error
                else "Ready"
            ),
        )

    if st.session_state.upload_in_progress:
        with st.spinner("Uploading and processing document..."):
            result = upload_document(uploaded_file)

        st.session_state.upload_in_progress = False
        if result.get("success"):
            st.session_state.upload_result = result
            st.session_state.upload_steps = ["complete"] * 5
        else:
            st.session_state.upload_error = result.get("error", "Unknown upload error")
            st.session_state.upload_steps = ["complete", "failed", "queued", "queued", "queued"]
        st.rerun()

    if st.session_state.upload_result:
        data = normalize_upload_data(st.session_state.upload_result)
        upload_success_panel(
            filename=data.get("filename") or uploaded_file.name,
            file_size=format_file_size(uploaded_file.size),
            total_chunks=data.get("total_chunks") or data.get("chunks_created") or "-",
            status=str(data.get("status") or "Processed").replace("_", " ").title(),
        )

        with st.expander("Backend response", expanded=False):
            st.json(st.session_state.upload_result.get("data", {}))

    if st.session_state.upload_error:
        st.error(f"Upload failed: {st.session_state.upload_error}")

st.markdown(
    """
    <section class="supported-types-panel">
        <div class="supported-types-title">Supported file types</div>
        <div class="supported-types-row">
            <span>TXT</span><span>PDF</span><span>DOCX</span><span>CSV</span><span>MD</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)
