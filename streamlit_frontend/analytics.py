"""
Pure helper functions that derive analytics from data the backend already
returns via /documents and /history. No backend changes required.
"""

from collections import Counter
from datetime import datetime


def safe_parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except Exception:
        return None


def document_stats(documents: list) -> dict:
    total = len(documents)
    processed = sum(1 for d in documents if d.get("status") == "processed")
    failed = sum(1 for d in documents if d.get("status") == "failed")
    processing = total - processed - failed
    total_chunks = sum((d.get("total_chunks") or 0) for d in documents)

    by_type = Counter(
        (d.get("file_type") or "unknown").lstrip(".").lower() or "unknown"
        for d in documents
    )

    return {
        "total": total,
        "processed": processed,
        "failed": failed,
        "processing": processing,
        "total_chunks": total_chunks,
        "by_type": dict(by_type),
    }


def history_stats(history: list) -> dict:
    total = len(history)
    if total == 0:
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "avg_latency_ms": 0,
            "min_latency_ms": 0,
            "max_latency_ms": 0,
            "p95_latency_ms": 0,
            "latencies": [],
            "top_questions": [],
        }

    success = sum(1 for h in history if h.get("status") == "success")
    failed = total - success

    latencies = sorted(
        h.get("latency_ms") for h in history if isinstance(h.get("latency_ms"), (int, float))
    )

    avg_latency = round(sum(latencies) / len(latencies)) if latencies else 0
    min_latency = latencies[0] if latencies else 0
    max_latency = latencies[-1] if latencies else 0

    if latencies:
        p95_index = max(0, int(len(latencies) * 0.95) - 1)
        p95_latency = latencies[p95_index]
    else:
        p95_latency = 0

    question_counter = Counter(
        (h.get("question") or "").strip().lower() for h in history if h.get("question")
    )
    top_questions = question_counter.most_common(5)

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "p95_latency_ms": p95_latency,
        "latencies": latencies,
        "top_questions": top_questions,
    }


def latency_timeseries(history: list):
    """
    Returns chronological (created_at, latency_ms) pairs for charting,
    oldest first. History from the backend is ordered newest-first, so we
    reverse it.
    """
    rows = []
    for item in reversed(history):
        ts = safe_parse_date(item.get("created_at"))
        latency = item.get("latency_ms")
        if ts is not None and isinstance(latency, (int, float)):
            rows.append({"time": ts, "latency_ms": latency})
    return rows


def questions_per_day(history: list):
    counts = Counter()
    for item in history:
        ts = safe_parse_date(item.get("created_at"))
        if ts:
            counts[ts.strftime("%Y-%m-%d")] += 1
    return dict(sorted(counts.items()))
