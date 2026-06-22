import html
import os
from time import perf_counter

import streamlit as st

from api_client import API_URL, check_backend_health, get_documents
from styles import apply_custom_css, page_header


st.set_page_config(
    page_title="Settings · Production Grade RAG System",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css()


MODEL_LABEL = os.getenv("MODEL_LABEL", "llama3.2:8b")
VECTOR_DB_LABEL = os.getenv("VECTOR_DB_LABEL", "ChromaDB")
DATABASE_LABEL = os.getenv("DATABASE_LABEL", "SQLite")


def safe(value, fallback="-"):
    if value is None or value == "":
        value = fallback
    return html.escape(str(value))


def environment_card(icon, label, value, badge=None, badge_kind="neutral"):
    badge_html = ""
    if badge:
        badge_html = (
            f'<span class="settings-card-badge settings-card-badge-{safe(badge_kind)}">'
            f'{safe(badge)}</span>'
        )
    st.markdown(
        '<article class="settings-environment-card">'
        f'<div class="settings-card-icon">{icon}</div>{badge_html}'
        f'<div class="settings-card-label">{safe(label)}</div>'
        f'<div class="settings-card-value">{safe(value)}</div>'
        '</article>',
        unsafe_allow_html=True,
    )


page_header(
    "CONFIGURATION",
    "Settings",
    "Backend connection, service stack, and local troubleshooting commands.",
    ["FastAPI", "Streamlit", "Ollama", "ChromaDB"],
)

health_started = perf_counter()
backend_healthy, backend_message = check_backend_health()
health_latency_ms = round((perf_counter() - health_started) * 1000)

documents_result = get_documents()
documents = documents_result.get("data", []) if documents_result.get("success") else []
processed_documents = sum(
    1
    for document in documents
    if str(document.get("status") or "").lower()
    in {"processed", "completed", "ready", "ingested", "success"}
)
indexed_chunks = sum(int(document.get("total_chunks") or 0) for document in documents)

st.markdown(
    '<div class="settings-section-head"><div>'
    '<div class="settings-section-title">Environment</div>'
    '<div class="settings-section-subtitle">Current backend connection and service stack</div></div>'
    f'<div class="settings-overall-health {"is-healthy" if backend_healthy else "is-offline"}">'
    f'{"Backend healthy" if backend_healthy else "Backend unavailable"}</div></div>',
    unsafe_allow_html=True,
)

environment_row_one = st.columns(3)
with environment_row_one[0]:
    environment_card("▣", "Backend URL", API_URL)
with environment_row_one[1]:
    environment_card(
        "ϟ",
        "Health Status",
        "Online" if backend_healthy else "Offline",
        badge="Live" if backend_healthy else "Down",
        badge_kind="success" if backend_healthy else "danger",
    )
with environment_row_one[2]:
    environment_card("▣", "Model", MODEL_LABEL)

environment_row_two = st.columns(3)
with environment_row_two[0]:
    environment_card("▤", "Vector Database", VECTOR_DB_LABEL)
with environment_row_two[1]:
    environment_card("▱", "Database", DATABASE_LABEL)
with environment_row_two[2]:
    environment_card("□", "Frontend", "Streamlit")

environment_row_three = st.columns(3)
with environment_row_three[0]:
    environment_card("⌘", "Backend", "FastAPI")

commands = [
    {
        "title": "Start Ollama",
        "description": "Launch the local model runtime",
        "command": "ollama serve",
    },
    {
        "title": "Start FastAPI backend",
        "description": "Boot the API gateway",
        "command": "uvicorn main:app --reload --port 8000",
    },
    {
        "title": "Start Streamlit frontend",
        "description": "Serve the user-facing application",
        "command": "streamlit run app.py",
    },
    {
        "title": "Check API endpoints",
        "description": "Verify backend health and connectivity",
        "command": f"curl {API_URL}/health",
    },
]

with st.container(key="settings_troubleshooting"):
    st.markdown(
        '<div class="settings-troubleshooting-head">'
        '<div class="settings-troubleshooting-icon">⌕</div><div>'
        '<div class="settings-troubleshooting-title">Troubleshooting</div>'
        '<div class="settings-troubleshooting-subtitle">Quick commands to restart services or verify health</div></div>'
        f'<a href="{safe(API_URL)}/docs" target="_blank">View docs ↗</a></div>',
        unsafe_allow_html=True,
    )

    for index, item in enumerate(commands):
        with st.container(key=f"settings_command_{index}"):
            icon_column, title_column, command_column, action_column = st.columns(
                [0.06, 0.25, 0.54, 0.15],
                vertical_alignment="center",
            )
            with icon_column:
                st.markdown('<div class="settings-command-icon">›_</div>', unsafe_allow_html=True)
            with title_column:
                st.markdown(
                    f'<div class="settings-command-title">{safe(item["title"])}</div>'
                    f'<div class="settings-command-description">{safe(item["description"])}</div>',
                    unsafe_allow_html=True,
                )
            with command_column:
                st.markdown(
                    f'<div class="settings-command-code">$ {safe(item["command"])}</div>',
                    unsafe_allow_html=True,
                )
            with action_column:
                if st.button(
                    "Run",
                    icon=":material/play_arrow:",
                    width="stretch",
                    key=f"show_command_{index}",
                    help="Show the command to run in your terminal",
                ):
                    st.session_state.settings_selected_command = item["command"]

selected_command = st.session_state.get("settings_selected_command")
if selected_command:
    st.info("Run this command in the appropriate terminal:")
    st.code(selected_command, language="bash")

st.markdown(
    '<section class="settings-health-summary">'
    '<div><span class="settings-health-icon">✓</span><p>API HEALTH LATENCY</p>'
    f'<strong>{health_latency_ms} ms</strong></div>'
    '<div><span class="settings-health-icon">✓</span><p>INDEXED CHUNKS</p>'
    f'<strong>{indexed_chunks:,}</strong></div>'
    '<div><span class="settings-health-icon">✓</span><p>DOCUMENTS READY</p>'
    f'<strong>{processed_documents:,} / {len(documents):,}</strong></div>'
    '</section>',
    unsafe_allow_html=True,
)

if not backend_healthy:
    st.warning(f"Backend health check failed: {backend_message}")

with st.expander("API routes and capability notes", expanded=False):
    st.code(
        """GET     /health
POST    /ask
POST    /upload
GET     /documents
GET     /history
DELETE  /documents/{id}  # required for document deletion""",
        language="text",
    )
    st.caption(
        "Delete remains unavailable until the backend implements DELETE /documents/{id}."
    )
