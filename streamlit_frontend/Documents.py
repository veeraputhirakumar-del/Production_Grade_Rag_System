import html
import mimetypes
from datetime import datetime
from pathlib import Path

import streamlit as st

from analytics import document_stats
from api_client import delete_document, get_document_details, get_documents
from styles import apply_custom_css, empty_state, metric_card, page_header


st.set_page_config(page_title="Documents · RAG Knowledge System", page_icon="◆", layout="wide")
apply_custom_css()


def safe(value, fallback="-"):
    if value is None or value == "":
        value = fallback
    return html.escape(str(value))


def display_document_id(document):
    document_id = str(document.get("id") or "-")
    return document_id if document_id.lower().startswith("doc_") else f"doc_{document_id}"


def file_type(document):
    value = str(document.get("file_type") or "").lstrip(".").upper()
    if value:
        return value
    filename = str(document.get("filename") or "")
    return filename.rsplit(".", 1)[-1].upper() if "." in filename else "FILE"


def normalized_status(document):
    value = str(document.get("status") or "processing").lower()
    if value in {"processed", "completed", "ready", "ingested", "success"}:
        return "Processed", "processed"
    if value in {"failed", "error"}:
        return "Failed", "failed"
    return "Processing", "processing"


def format_date(value):
    if not value:
        return "-"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%b %d, %Y")
    except (TypeError, ValueError):
        return str(value)


def local_download(document):
    path_value = document.get("file_path")
    if not path_value:
        return None
    path = Path(path_value)
    try:
        if path.is_file() and path.stat().st_size <= 50 * 1024 * 1024:
            return path.read_bytes()
    except OSError:
        return None
    return None


def type_badge(value):
    badge_class = value.lower() if value.lower() in {"pdf", "md", "docx", "csv", "txt"} else "file"
    return f'<span class="document-type-badge type-{badge_class}">{safe(value)}</span>'


def status_badge(label, status_class):
    return f'<span class="document-table-status status-{status_class}">{safe(label)}</span>'


def render_document_viewer(document_id, fallback_document):
    cache = st.session_state.setdefault("document_details_cache", {})
    if document_id not in cache:
        cache[document_id] = get_document_details(document_id)

    result = cache[document_id]
    if not result.get("success"):
        st.error(result.get("error", "Could not load indexed document details."))
        if st.button("Retry details", key=f"retry_details_{document_id}"):
            cache.pop(document_id, None)
            st.rerun()
        return

    payload = result.get("data", {})
    document = payload.get("document") or fallback_document
    chunks = payload.get("chunks") or []
    embedding_model = payload.get("embedding_model") or "-"
    vector_db = payload.get("vector_db") or "ChromaDB"
    dimensions = sorted({
        int(chunk.get("embedding_dimension") or 0)
        for chunk in chunks
        if chunk.get("embedding_dimension")
    })
    dimension_label = ", ".join(str(value) for value in dimensions) if dimensions else "-"

    st.markdown(
        '<div class="document-viewer-head"><div>'
        '<div class="document-viewer-title">Indexed document viewer</div>'
        f'<div class="document-viewer-subtitle">{safe(document.get("filename"))}</div></div>'
        f'<span>{len(chunks)} chunks</span></div>',
        unsafe_allow_html=True,
    )

    summary_columns = st.columns(4)
    summary_columns[0].metric("Chunks", len(chunks))
    summary_columns[1].metric("Vector DB", vector_db)
    summary_columns[2].metric("Dimensions", dimension_label)
    summary_columns[3].metric("Status", normalized_status(document)[0])

    content_tab, chunks_tab, metadata_tab = st.tabs(
        ["Indexed content", "Chunks & embeddings", "Metadata"]
    )

    with content_tab:
        if chunks:
            content_html = "".join(
                '<section class="indexed-content-chunk">'
                f'<div>Chunk #{safe(chunk.get("chunk_index"))} · Page {safe(chunk.get("page_number"))}</div>'
                f'<p>{safe(chunk.get("chunk_text"))}</p></section>'
                for chunk in chunks
            )
            st.markdown(
                f'<div class="indexed-content-scroll">{content_html}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No SQLite chunks were found for this document.")

    with chunks_tab:
        for chunk in chunks:
            chunk_index = chunk.get("chunk_index")
            dimension = int(chunk.get("embedding_dimension") or 0)
            label = (
                f"Chunk #{chunk_index} · Page {chunk.get('page_number') or '-'} · "
                f"{dimension or '-'} dimensions"
            )
            with st.expander(label, expanded=chunk_index == 0):
                st.markdown(chunk.get("chunk_text") or "No chunk text")
                vector_preview = chunk.get("embedding_preview") or []
                details_columns = st.columns(3)
                details_columns[0].caption(f"Chroma ID: {chunk.get('chroma_id') or '-'}")
                details_columns[1].caption(f"L2 norm: {chunk.get('embedding_norm', 0)}")
                details_columns[2].caption(f"Model: {embedding_model}")
                if vector_preview:
                    st.caption("Embedding preview (first vector values)")
                    st.code("[" + ", ".join(str(value) for value in vector_preview) + ", ...]")
                else:
                    st.warning("No matching vector was found in ChromaDB for this chunk.")

    with metadata_tab:
        st.json({
            "document": document,
            "embedding_model": embedding_model,
            "vector_database": vector_db,
        })


page_header(
    "KNOWLEDGE BASE",
    "Documents",
    "Browse, search, and manage every file that has been ingested into the retrieval index.",
    ["Search", "Filter by Status", "Filter by Type"],
)

result = get_documents()
documents = result.get("data", [])

if not result.get("success"):
    st.error("Could not load documents from the backend.")
    st.code(result.get("error", "Unknown error"))
    st.stop()

stats = document_stats(documents)

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total", stats["total"], "All uploaded files")
with col2:
    metric_card("Processed", stats["processed"], "Ready for retrieval")
with col3:
    metric_card("Processing", stats["processing"], "Still being indexed")
with col4:
    metric_card("Failed", stats["failed"], "Ingestion errors")

if not documents:
    st.markdown('<div class="documents-section-gap"></div>', unsafe_allow_html=True)
    empty_state("No documents uploaded yet", "Go to the Upload page to add your first file.", "○")
    st.stop()

with st.container(key="document_filters"):
    filter_col1, filter_col2, filter_col3 = st.columns([0.5, 0.25, 0.25])
    with filter_col1:
        search = st.text_input("Search by filename", placeholder="Search documents...")
    with filter_col2:
        status_options = ["All"] + sorted({normalized_status(document)[0] for document in documents})
        status_filter = st.selectbox("Status", status_options)
    with filter_col3:
        type_options = ["All"] + sorted({file_type(document) for document in documents})
        type_filter = st.selectbox("File type", type_options)

filtered = documents
if search:
    filtered = [
        document
        for document in filtered
        if search.lower() in str(document.get("filename") or "").lower()
    ]
if status_filter != "All":
    filtered = [document for document in filtered if normalized_status(document)[0] == status_filter]
if type_filter != "All":
    filtered = [document for document in filtered if file_type(document) == type_filter]

st.markdown(
    f'<div class="documents-count">Showing {len(filtered)} of {len(documents)} documents</div>',
    unsafe_allow_html=True,
)

if not filtered:
    empty_state("No matches", "Try adjusting your search or filters.", "○")
    st.stop()

with st.container(key="documents_table"):
    with st.container(key="documents_table_header"):
        header_columns = st.columns([0.34, 0.13, 0.15, 0.11, 0.16, 0.15])
        for column, label in zip(
            header_columns,
            ["FILENAME", "TYPE", "STATUS", "CHUNKS", "UPLOADED", "ACTIONS"],
        ):
            column.markdown(f'<div class="document-column-label">{label}</div>', unsafe_allow_html=True)

    for index, document in enumerate(filtered):
        document_id = document.get("id")
        filename = document.get("filename") or "Unknown file"
        type_label = file_type(document)
        status_label, status_class = normalized_status(document)
        download_data = local_download(document)

        with st.container(key=f"document_row_{index}"):
            row_columns = st.columns([0.34, 0.13, 0.15, 0.11, 0.16, 0.15], vertical_alignment="center")

            with row_columns[0]:
                st.markdown(
                    '<div class="document-table-file"><div class="document-table-icon">▤</div><div class="document-table-file-copy">'
                    f'<div class="document-table-name" title="{safe(filename)}">{safe(filename)}</div>'
                    f'<div class="document-table-id">{safe(display_document_id(document))}</div>'
                    '</div></div>',
                    unsafe_allow_html=True,
                )
            with row_columns[1]:
                st.markdown(type_badge(type_label), unsafe_allow_html=True)
            with row_columns[2]:
                st.markdown(status_badge(status_label, status_class), unsafe_allow_html=True)
            with row_columns[3]:
                st.markdown(
                    f'<div class="document-chunk-count">{int(document.get("total_chunks") or 0):,}</div>',
                    unsafe_allow_html=True,
                )
            with row_columns[4]:
                st.markdown(
                    f'<div class="document-upload-date">{safe(format_date(document.get("created_at")))}</div>',
                    unsafe_allow_html=True,
                )
            with row_columns[5]:
                actions = st.columns(4, gap="small")
                with actions[0]:
                    if st.button(
                        "",
                        icon=":material/visibility:",
                        help="View details",
                        key=f"view_{document_id}_{index}",
                    ):
                        current = st.session_state.get("view_document_id")
                        st.session_state.view_document_id = None if current == document_id else document_id
                        st.rerun()
                with actions[1]:
                    if download_data is not None:
                        st.download_button(
                            "",
                            data=download_data,
                            file_name=filename,
                            mime=mimetypes.guess_type(filename)[0] or "application/octet-stream",
                            icon=":material/download:",
                            help="Download file",
                            key=f"download_{document_id}_{index}",
                        )
                    else:
                        st.button(
                            "",
                            icon=":material/download:",
                            help="File is stored on the backend and is not locally downloadable",
                            disabled=True,
                            key=f"download_disabled_{document_id}_{index}",
                        )
                with actions[2]:
                    if st.button(
                        "",
                        icon=":material/delete:",
                        help="Delete document",
                        key=f"delete_{document_id}_{index}",
                    ):
                        st.session_state.delete_document_id = document_id
                        st.rerun()
                with actions[3]:
                    with st.popover("⋯", help="More details"):
                        st.caption("File path")
                        st.code(document.get("file_path") or "No path available")
                        st.caption(f"Document ID: {document_id}")

            if st.session_state.get("view_document_id") == document_id:
                with st.container(key=f"document_viewer_{index}"):
                    render_document_viewer(document_id, document)

            if st.session_state.get("delete_document_id") == document_id:
                st.warning(f'Delete "{filename}"? This cannot be undone.')
                confirm_col, cancel_col, spacer = st.columns([0.13, 0.13, 0.74])
                with confirm_col:
                    if st.button("Delete", type="primary", width="stretch", key=f"confirm_{document_id}_{index}"):
                        outcome = delete_document(document_id)
                        if outcome.get("success"):
                            st.session_state.delete_document_id = None
                            st.rerun()
                        st.error(outcome.get("error", "Could not delete document."))
                with cancel_col:
                    if st.button("Cancel", width="stretch", key=f"cancel_{document_id}_{index}"):
                        st.session_state.delete_document_id = None
                        st.rerun()

if stats.get("by_type"):
    st.markdown('<div class="documents-section-gap"></div>', unsafe_allow_html=True)
    st.markdown("##### By file type")
    type_columns = st.columns(max(len(stats["by_type"]), 1))
    for column, (extension, count) in zip(type_columns, stats["by_type"].items()):
        with column:
            metric_card(extension.upper() or "UNKNOWN", count, "documents")
