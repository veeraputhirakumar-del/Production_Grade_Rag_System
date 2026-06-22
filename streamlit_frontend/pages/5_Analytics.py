import html
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from analytics import document_stats, history_stats, latency_timeseries, questions_per_day
from api_client import get_documents, get_question_history
from styles import apply_custom_css, empty_state, metric_card, page_header


st.set_page_config(
    page_title="Analytics · Production Grade RAG System",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css()


PERIODS = {
    "All time": None,
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
}


def parse_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def answered(item):
    return str(item.get("status") or "success").lower() in {
        "success",
        "answered",
        "completed",
    }


def source_count(item):
    sources = item.get("sources")
    if isinstance(sources, list):
        return len(sources)
    for key in ("source_count", "sources_count", "retrieved_sources"):
        try:
            if item.get(key) is not None:
                return int(item[key])
        except (TypeError, ValueError):
            pass
    return 0


def latency_value(item):
    try:
        return max(0.0, float(item.get("latency_ms") or 0))
    except (TypeError, ValueError):
        return 0.0


def empty_question_stats():
    return {
        "total": 0,
        "success": 0,
        "avg_latency_ms": 0,
        "p95_latency_ms": 0,
        "max_latency_ms": 0,
        "top_questions": [],
    }


def compact_number(value):
    value = int(value or 0)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def latency_distribution(history):
    buckets = {
        "< 1s": 0,
        "1-2s": 0,
        "2-5s": 0,
        "5-10s": 0,
        "> 10s": 0,
    }
    for item in history:
        latency = latency_value(item)
        if latency < 1000:
            buckets["< 1s"] += 1
        elif latency < 2000:
            buckets["1-2s"] += 1
        elif latency < 5000:
            buckets["2-5s"] += 1
        elif latency < 10000:
            buckets["5-10s"] += 1
        else:
            buckets["> 10s"] += 1
    return buckets


def recent_query_rows(history):
    rows = []
    sorted_history = sorted(
        history,
        key=lambda item: parse_datetime(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    for item in sorted_history[:10]:
        created_at = parse_datetime(item.get("created_at"))
        rows.append(
            {
                "Asked": created_at.strftime("%b %d, %H:%M") if created_at else "-",
                "Question": item.get("question") or "No question",
                "Status": "Answered" if answered(item) else "Failed",
                "Latency": f"{latency_value(item) / 1000:.2f}s",
                "Sources": source_count(item),
            }
        )
    return rows


page_header(
    "INSIGHTS",
    "Analytics",
    "Usage, retrieval activity, and performance trends across your knowledge base.",
    ["Latency", "Volume", "Knowledge Base", "Query Performance"],
)

docs_result = get_documents()
history_result = get_question_history()

if not docs_result.get("success") or not history_result.get("success"):
    st.error("Could not load analytics data from the backend.")
    if not docs_result.get("success"):
        st.caption(docs_result.get("error", "Document request failed"))
    if not history_result.get("success"):
        st.caption(history_result.get("error", "History request failed"))
    st.stop()

documents = docs_result.get("data", [])
history = history_result.get("data", [])

with st.container(key="analytics_filters"):
    period_column, status_column, summary_column = st.columns([0.28, 0.28, 0.44])
    with period_column:
        selected_period = st.selectbox("Time period", list(PERIODS.keys()), index=0)
    with status_column:
        selected_status = st.selectbox("Question status", ["All", "Answered", "Failed"])
    with summary_column:
        st.markdown(
            f'<div class="analytics-filter-summary">{len(history):,} total questions · '
            f'{len(documents):,} indexed documents</div>',
            unsafe_allow_html=True,
        )

filtered_history = history
period_days = PERIODS[selected_period]
if period_days is not None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
    filtered_history = [
        item
        for item in filtered_history
        if (parse_datetime(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= cutoff
    ]
if selected_status == "Answered":
    filtered_history = [item for item in filtered_history if answered(item)]
elif selected_status == "Failed":
    filtered_history = [item for item in filtered_history if not answered(item)]

doc_stats = document_stats(documents)
q_stats = history_stats(filtered_history) if filtered_history else empty_question_stats()
success_rate = round(100 * q_stats["success"] / q_stats["total"]) if q_stats["total"] else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    metric_card("Questions", q_stats["total"], selected_period)
with kpi2:
    metric_card("Success Rate", f"{success_rate}%", "Answered without error")
with kpi3:
    metric_card("Avg Latency", f"{q_stats['avg_latency_ms']} ms", "Mean response time")
with kpi4:
    metric_card("P95 Latency", f"{q_stats['p95_latency_ms']} ms", "Slowest 5% threshold")

per_day = questions_per_day(filtered_history) if filtered_history else {}
busiest_day = max(per_day, key=per_day.get) if per_day else "-"
average_sources = (
    sum(source_count(item) for item in filtered_history) / len(filtered_history)
    if filtered_history
    else 0
)
average_chunks = (
    round(doc_stats["total_chunks"] / doc_stats["processed"], 1)
    if doc_stats["processed"]
    else 0
)

st.markdown(
    '<section class="analytics-health-strip">'
    f'<div><span>Indexed documents</span><strong>{doc_stats["processed"]:,}</strong></div>'
    f'<div><span>Searchable chunks</span><strong>{compact_number(doc_stats["total_chunks"])}</strong></div>'
    f'<div><span>Avg. chunks / document</span><strong>{average_chunks}</strong></div>'
    f'<div><span>Avg. sources / answer</span><strong>{average_sources:.1f}</strong></div>'
    f'<div><span>Busiest day</span><strong>{html.escape(str(busiest_day))}</strong></div>'
    '</section>',
    unsafe_allow_html=True,
)

if not filtered_history:
    empty_state(
        "No activity for these filters",
        "Choose a wider time period or a different status.",
        "○",
    )
else:
    latency_column, volume_column = st.columns([0.56, 0.44])

    with latency_column:
        with st.container(key="analytics_latency_chart"):
            st.markdown(
                '<div class="analytics-panel-title">Latency over time</div>'
                '<div class="analytics-panel-subtitle">Response duration for each question</div>',
                unsafe_allow_html=True,
            )
            latency_series = latency_timeseries(filtered_history)
            if latency_series:
                latency_frame = pd.DataFrame(latency_series).set_index("time")
                st.line_chart(latency_frame, height=280, width="stretch")
            else:
                st.caption("Not enough timestamped data to chart yet.")

    with volume_column:
        with st.container(key="analytics_volume_chart"):
            st.markdown(
                '<div class="analytics-panel-title">Questions per day</div>'
                '<div class="analytics-panel-subtitle">Daily query volume</div>',
                unsafe_allow_html=True,
            )
            if per_day:
                volume_frame = pd.DataFrame(
                    list(per_day.items()),
                    columns=["date", "questions"],
                ).set_index("date")
                st.bar_chart(volume_frame, height=280, width="stretch")
            else:
                st.caption("Not enough timestamped data to chart yet.")

    latency_bucket_column, status_column = st.columns([0.56, 0.44])
    with latency_bucket_column:
        with st.container(key="analytics_distribution_chart"):
            st.markdown(
                '<div class="analytics-panel-title">Latency distribution</div>'
                '<div class="analytics-panel-subtitle">Questions grouped by response time</div>',
                unsafe_allow_html=True,
            )
            distribution = latency_distribution(filtered_history)
            distribution_frame = pd.DataFrame(
                list(distribution.items()),
                columns=["latency", "questions"],
            ).set_index("latency")
            st.bar_chart(distribution_frame, height=240, width="stretch")

    with status_column:
        with st.container(key="analytics_query_status"):
            st.markdown(
                '<div class="analytics-panel-title">Query outcomes</div>'
                '<div class="analytics-panel-subtitle">Answered and failed requests</div>',
                unsafe_allow_html=True,
            )
            outcome_frame = pd.DataFrame(
                {
                    "status": ["Answered", "Failed"],
                    "questions": [q_stats["success"], q_stats["total"] - q_stats["success"]],
                }
            ).set_index("status")
            st.bar_chart(outcome_frame, height=240, width="stretch")

knowledge_status_column, knowledge_type_column = st.columns(2)
with knowledge_status_column:
    with st.container(key="analytics_document_status"):
        st.markdown(
            '<div class="analytics-panel-title">Document status</div>'
            '<div class="analytics-panel-subtitle">Current ingestion outcomes</div>',
            unsafe_allow_html=True,
        )
        status_frame = pd.DataFrame(
            {
                "status": ["Processed", "Processing", "Failed"],
                "documents": [
                    doc_stats["processed"],
                    doc_stats["processing"],
                    doc_stats["failed"],
                ],
            }
        ).set_index("status")
        st.bar_chart(status_frame, height=240, width="stretch")

with knowledge_type_column:
    with st.container(key="analytics_document_types"):
        st.markdown(
            '<div class="analytics-panel-title">Documents by file type</div>'
            '<div class="analytics-panel-subtitle">Knowledge-base composition</div>',
            unsafe_allow_html=True,
        )
        if doc_stats["by_type"]:
            type_frame = pd.DataFrame(
                list(doc_stats["by_type"].items()),
                columns=["type", "documents"],
            ).set_index("type")
            st.bar_chart(type_frame, height=240, width="stretch")
        else:
            st.caption("No documents uploaded yet.")

top_column, recent_column = st.columns([0.4, 0.6])
with top_column:
    with st.container(key="analytics_top_questions"):
        st.markdown(
            '<div class="analytics-panel-title">Frequently asked</div>'
            '<div class="analytics-panel-subtitle">Repeated questions in the selected period</div>',
            unsafe_allow_html=True,
        )
        if q_stats["top_questions"]:
            for rank, (question, count) in enumerate(q_stats["top_questions"][:6], start=1):
                st.markdown(
                    '<div class="analytics-question-row">'
                    f'<span class="analytics-question-rank">{rank}</span>'
                    f'<span class="analytics-question-text">{html.escape(str(question))}</span>'
                    f'<strong>{count}×</strong></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No repeated questions yet.")

with recent_column:
    with st.container(key="analytics_recent_queries"):
        st.markdown(
            '<div class="analytics-panel-title">Recent query performance</div>'
            '<div class="analytics-panel-subtitle">Latest questions and response metrics</div>',
            unsafe_allow_html=True,
        )
        recent_rows = recent_query_rows(filtered_history)
        if recent_rows:
            st.dataframe(
                pd.DataFrame(recent_rows),
                hide_index=True,
                width="stretch",
                height=290,
                column_config={
                    "Question": st.column_config.TextColumn("Question", width="large"),
                    "Sources": st.column_config.NumberColumn("Sources", format="%d"),
                },
            )
        else:
            st.caption("No recent queries for these filters.")
