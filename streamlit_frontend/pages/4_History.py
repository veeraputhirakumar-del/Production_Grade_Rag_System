import html
from datetime import datetime

import streamlit as st

from analytics import history_stats
from api_client import get_question_history
from styles import apply_custom_css, empty_state, metric_card, page_header


st.set_page_config(
    page_title="History · Production Grade RAG System",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css()


def safe(value, fallback="-"):
    if value is None or value == "":
        value = fallback
    return html.escape(str(value))


def format_timestamp(value):
    if not value:
        return "-"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%b %d, %Y · %H:%M")
    except (TypeError, ValueError):
        return str(value)


def format_latency(value):
    try:
        return f"{float(value) / 1000:.2f}s"
    except (TypeError, ValueError):
        return "-"


def source_count(item):
    sources = item.get("sources")
    if isinstance(sources, list):
        return len(sources)
    for key in ("source_count", "sources_count", "retrieved_sources"):
        if item.get(key) is not None:
            try:
                return int(item[key])
            except (TypeError, ValueError):
                pass
    return 0


def normalized_status(item):
    value = str(item.get("status") or "success").lower()
    if value in {"success", "answered", "completed"}:
        return "Answered", "answered"
    if value in {"failed", "error"}:
        return "Failed", "failed"
    return value.title(), "pending"


def history_tags(item, sources_found):
    tags = ["✦ RAG Answer"]
    if sources_found:
        tags.append("✦ With Sources")
    mode = item.get("answer_mode") or item.get("mode")
    if mode and str(mode).lower() != "normal":
        tags.append(f"✦ {str(mode).title()}")
    return "".join(f'<span class="history-tag">{safe(tag)}</span>' for tag in tags)


page_header(
    "RECORDS",
    "Question History",
    "Review previous questions, answers, latency, and backend status for each request.",
    ["SQLite Log", "Latest 50", "Latency Tracking"],
)

result = get_question_history()

if not result.get("success"):
    st.error("Could not load question history.")
    st.code(result.get("error", "Unknown error"))
    st.stop()

history = result.get("data", [])

if not history:
    empty_state("No questions yet", "Ask something from the Chat page to populate this list.", "○")
    st.stop()

stats = history_stats(history)

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Questions", stats["total"], "Logged in this window")
with col2:
    success_rate = round(100 * stats["success"] / stats["total"]) if stats["total"] else 0
    metric_card("Success Rate", f"{success_rate}%", "Answered without error")
with col3:
    metric_card("Avg Latency", f"{stats['avg_latency_ms']} ms", "Across all questions")
with col4:
    metric_card("P95 Latency", f"{stats['p95_latency_ms']} ms", "Slowest 5% of requests")

with st.container(key="history_search"):
    search = st.text_input(
        "Search history",
        placeholder="Search questions and answers...",
    )

filtered = history
if search:
    search_term = search.lower()
    filtered = [
        item
        for item in history
        if search_term in str(item.get("question") or "").lower()
        or search_term in str(item.get("answer") or "").lower()
    ]

st.markdown(
    f'<div class="history-count">Showing {len(filtered)} of {len(history)} questions</div>',
    unsafe_allow_html=True,
)

if not filtered:
    empty_state("No matches", "Try a different search term.", "○")
    st.stop()

for index, item in enumerate(filtered):
    item_id = item.get("id") if item.get("id") is not None else index
    question = item.get("question") or "No question"
    answer = item.get("answer") or "No answer was recorded."
    sources_found = source_count(item)
    status_label, status_class = normalized_status(item)
    expanded = st.session_state.get("expanded_history_id") == item_id

    with st.container(key=f"history_card_{index}"):
        icon_column, content_column, status_column = st.columns(
            [0.06, 0.82, 0.12],
            vertical_alignment="top",
        )

        with icon_column:
            st.markdown('<div class="history-card-icon">▢</div>', unsafe_allow_html=True)

        with content_column:
            st.markdown(
                '<div class="history-meta">'
                f'<span>{safe(format_timestamp(item.get("created_at")))}</span>'
                '<span class="history-meta-dot">·</span>'
                f'<span>◔ {safe(format_latency(item.get("latency_ms")))}</span>'
                '<span class="history-meta-dot">·</span>'
                f'<span>▤ {sources_found} source{"s" if sources_found != 1 else ""}</span>'
                '</div>'
                f'<div class="history-question">{safe(question)}</div>'
                f'<div class="history-answer-preview">{safe(answer)}</div>',
                unsafe_allow_html=True,
            )

        with status_column:
            st.markdown(
                f'<div class="history-status-wrap"><span class="history-status history-status-{status_class}">'
                f'{safe(status_label)}</span></div>',
                unsafe_allow_html=True,
            )

        tags_column, action_column = st.columns([0.76, 0.24], vertical_alignment="center")
        with tags_column:
            st.markdown(
                f'<div class="history-tags">{history_tags(item, sources_found)}</div>',
                unsafe_allow_html=True,
            )
        with action_column:
            button_label = "Collapse answer ↑" if expanded else "Expand answer →"
            if st.button(button_label, key=f"expand_history_{item_id}_{index}"):
                st.session_state.expanded_history_id = None if expanded else item_id
                st.rerun()

        if expanded:
            st.markdown('<div class="history-expanded-divider"></div>', unsafe_allow_html=True)
            st.markdown(answer)
            detail_columns = st.columns(3)
            detail_columns[0].caption(f"Question ID: {item_id}")
            detail_columns[1].caption(f"Latency: {format_latency(item.get('latency_ms'))}")
            detail_columns[2].caption(f"Sources: {sources_found}")
