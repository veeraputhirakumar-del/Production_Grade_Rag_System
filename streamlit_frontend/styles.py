"""Shared visual components for the Production Grade RAG System frontend."""

import html
import os
from datetime import datetime, timezone

import streamlit as st
import streamlit.components.v1 as components


def _safe(value, fallback="-"):
    if value is None or value == "":
        value = fallback
    return html.escape(str(value))


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _relative_time(value):
    parsed = _parse_datetime(value)
    if not parsed:
        return _safe(value)
    seconds = max(0, int((datetime.now(timezone.utc) - parsed).total_seconds()))
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} min ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hr{'s' if hours != 1 else ''} ago"
    days = seconds // 86400
    return f"{days} day{'s' if days != 1 else ''} ago"


def _document_type(document):
    file_type = str(document.get("file_type") or "").lstrip(".").upper()
    if file_type:
        return file_type
    filename = str(document.get("filename") or "")
    return filename.rsplit(".", 1)[-1].upper() if "." in filename else "FILE"


def _document_status(document):
    raw = str(document.get("status") or "processing").lower()
    if raw in {"processed", "completed", "ingested", "ready", "success"}:
        return "Processed", "processed"
    if raw in {"failed", "error"}:
        return "Failed", "failed"
    return "Processing", "processing"


def apply_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,0,0');

        :root {
            --bg: #0d111c;
            --surface: #151a26;
            --surface-raised: #1a2030;
            --border: #272e3d;
            --text: #f4f6fb;
            --muted: #9eb0d3;
            --faint: #7f8ba2;
            --accent: #7467ff;
            --accent-blue: #459cff;
            --danger: #ff4658;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp { background: var(--bg); color: var(--text); }
        section[data-testid="stSidebar"] {
            position: relative;
            height: 100dvh !important;
            max-height: 100dvh !important;
            overflow: hidden !important;
            background: #0d1220;
            border-right: 1px solid #263047;
            box-shadow: 12px 0 34px rgba(3, 7, 18, .18);
        }
        section[data-testid="stSidebar"]::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 18% 4%, rgba(116,103,255,.11), transparent 24%),
                linear-gradient(180deg, #111727 0%, #0d1220 62%);
            z-index: 0;
            pointer-events: none;
        }
        section[data-testid="stSidebar"] * { color: var(--text); }
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            position: relative;
            height: 100dvh !important;
            max-height: 100dvh !important;
            overflow: hidden !important;
            scrollbar-width: none !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"]::-webkit-scrollbar,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] > div::-webkit-scrollbar {
            display: none !important;
            width: 0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            position: fixed;
            top: 154px;
            bottom: 10px;
            left: 0;
            width: 300px;
            z-index: 2;
            height: auto !important;
            max-height: none !important;
            padding: 7px 14px;
            overflow: hidden !important;
            scrollbar-width: none !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] > div {
            height: auto !important;
            max-height: none !important;
            overflow: hidden !important;
            scrollbar-width: none !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul {
            display: flex;
            flex-direction: column;
            justify-content: flex-start !important;
            gap: 3px !important;
            height: auto !important;
            max-height: none !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li {
            flex: 0 0 auto;
            margin: 0 !important;
            padding: 0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
            height: 40px !important;
            min-height: 40px !important;
            max-height: 40px !important;
            display: flex;
            align-items: center;
            gap: 11px;
            padding: 6px 12px !important;
            border: 1px solid transparent;
            border-radius: 8px;
            color: #9ca9c0;
            font-size: 13px;
            font-weight: 600;
            transition: transform .15s ease, background .15s ease, border-color .15s ease, color .15s ease;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
            transform: translateX(2px);
            border-color: #2f3950;
            background: rgba(27,35,51,.88);
            color: #fff;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
            border-color: rgba(123,114,255,.42);
            background: linear-gradient(90deg, rgba(116,103,255,.21), rgba(69,156,255,.08));
            color: #fff;
            font-weight: 700;
            box-shadow: inset 3px 0 0 #8178ff, 0 8px 18px rgba(4,8,20,.17);
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li a::before {
            width: 22px;
            height: 22px;
            flex: 0 0 22px;
            display: grid;
            place-items: center;
            border-radius: 6px;
            color: #8992ff;
            font-size: 15px;
            text-align: center;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"]::before {
            background: rgba(129,120,255,.16);
            color: #aaa4ff;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:nth-child(1) a::before { content: "▦"; }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:nth-child(2) a::before { content: "◇"; }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:nth-child(3) a::before { content: "⇧"; }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:nth-child(4) a::before { content: "▤"; }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:nth-child(5) a::before { content: "◷"; }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:nth-child(6) a::before { content: "⌁"; }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:nth-child(7) a::before { content: "⚙"; }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child a span {
            display: none !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child a::after {
            content: "Dashboard";
            font-size: 13px;
            font-weight: 650;
            color: inherit;
        }
        .sidebar-brand-panel {
            position: fixed;
            top: 8px;
            left: 12px;
            width: 276px;
            padding: 11px 13px;
            border: 1px solid #303a51;
            border-radius: 10px;
            background: linear-gradient(145deg, rgba(27,35,54,.98), rgba(18,25,39,.98));
            box-shadow: 0 14px 32px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.035);
            z-index: 5;
            pointer-events: none;
        }
        .sidebar-brand-panel::before {
            content: "";
            position: absolute;
            top: -1px;
            left: 18px;
            right: 18px;
            height: 2px;
            border-radius: 99px;
            background: linear-gradient(90deg, #786cff, #42a5ff);
        }
        .sidebar-product-brand {
            position: static;
            width: auto;
            display: grid;
            grid-template-columns: 42px minmax(0, 1fr);
            align-items: center;
            gap: 12px;
        }
        .sidebar-product-mark {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border: 1px solid rgba(156,161,255,.5);
            border-radius: 9px;
            background: linear-gradient(145deg, #776cff, #459cff);
            color: #fff;
            font-size: 18px;
            font-weight: 800;
            box-shadow: 0 8px 20px rgba(86,111,255,.26);
        }
        .sidebar-product-name {
            color: #fff;
            font-size: 14px;
            font-weight: 800;
            line-height: 1.22;
        }
        .sidebar-product-subtitle {
            color: #8d9bb5;
            font-size: 9px;
            font-weight: 650;
            letter-spacing: .65px;
            margin-top: 4px;
            text-transform: uppercase;
        }
        .sidebar-status-chips {
            position: static;
            width: auto;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
        }
        .sidebar-health-chip,
        .sidebar-model-chip {
            display: inline-flex;
            align-items: center;
            min-height: 23px;
            padding: 3px 8px;
            border-radius: 999px;
            font-size: 9px;
            font-weight: 700;
            white-space: nowrap;
        }
        .sidebar-health-chip {
            border: 1px solid rgba(83,207,146,.42);
            color: #8be0b2;
            background: rgba(36,121,81,.12);
        }
        .sidebar-health-chip::before { content: ""; width: 6px; height: 6px; margin-right: 6px; border-radius: 50%; background: #55d394; box-shadow: 0 0 0 3px rgba(85,211,148,.1); }
        .sidebar-health-chip.is-offline { border-color: rgba(255,70,88,.45); color: #ff5263; }
        .sidebar-health-chip.is-offline::before { background: #ff5263; box-shadow: 0 0 0 3px rgba(255,82,99,.1); }
        .sidebar-model-chip {
            border: 1px solid #2b3242;
            background: #171f2f;
            color: #aab5c9;
        }
        .sidebar-workspace-label {
            position: fixed;
            top: 132px;
            left: 27px;
            color: #78859b;
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 1.05px;
            text-transform: uppercase;
            z-index: 4;
            pointer-events: none;
        }
        .sidebar-workspace-label::after {
            content: "";
            display: inline-block;
            width: 132px;
            height: 1px;
            margin: 0 0 3px 10px;
            background: linear-gradient(90deg, #2f394d, transparent);
        }
        .sidebar-environment-card {
            display: none !important;
        }
        .sidebar-environment-label { color: #7e8ba2; font-size: 8px; font-weight: 800; letter-spacing: .75px; text-transform: uppercase; }
        .sidebar-environment-title { color: #eef1f7; font-size: 12px; font-weight: 700; margin-top: 5px; }
        .sidebar-environment-copy { color: #8290a9; font-size: 9px; margin-top: 3px; }

        @media (max-height: 720px) {
            .sidebar-brand-panel { padding: 9px 12px; }
            .sidebar-product-mark { width: 38px; height: 38px; }
            .sidebar-product-brand { grid-template-columns: 38px minmax(0, 1fr); gap: 9px; }
            .sidebar-product-name { font-size: 12px; }
            .sidebar-product-subtitle { font-size: 8px; }
            .sidebar-status-chips { margin-top: 6px; }
            .sidebar-workspace-label { top: 116px; }
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { top: 134px; bottom: 6px; }
            section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
                height: 36px !important;
                min-height: 36px !important;
                max-height: 36px !important;
                padding-top: 4px !important;
                padding-bottom: 4px !important;
            }
        }

        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1440px;
        }
        h1, h2, h3, h4 { color: var(--text); letter-spacing: 0; }
        hr, div[data-testid="stDivider"] { border-color: var(--border) !important; }

        .page-header {
            padding-bottom: 18px;
            margin-bottom: 22px;
            border-bottom: 1px solid var(--border);
        }
        .page-eyebrow {
            color: var(--accent);
            font-size: 12.5px;
            font-weight: 600;
            letter-spacing: 1.2px;
            margin-bottom: 6px;
        }
        .page-title { font-size: 28px; font-weight: 700; line-height: 1.25; margin: 0; }
        .page-subtitle { margin-top: 8px; color: var(--muted); font-size: 14.5px; line-height: 1.55; }
        .tag-row { margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px; }
        .tag {
            padding: 4px 10px;
            border-radius: 6px;
            background: var(--surface-raised);
            border: 1px solid var(--border);
            color: var(--muted);
            font-size: 12px;
            font-weight: 500;
        }

        .metric-card {
            padding: 18px 20px;
            border-radius: 8px;
            background: var(--surface);
            border: 1px solid var(--border);
            min-height: 104px;
        }
        .metric-label { color: var(--muted); font-size: 12.5px; font-weight: 600; text-transform: uppercase; }
        .metric-value { color: var(--text); font-size: 28px; font-weight: 700; margin-top: 6px; line-height: 1.2; }
        .metric-help { color: var(--faint); font-size: 12.5px; margin-top: 4px; }
        .metric-delta-up { color: #3fb97f; font-size: 12.5px; font-weight: 600; }
        .metric-delta-down { color: var(--danger); font-size: 12.5px; font-weight: 600; }

        .pill { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
        .pill-success { background: rgba(63,185,127,.12); color: #3fb97f; }
        .pill-warning { background: rgba(217,164,65,.12); color: #d9a441; }
        .pill-danger { background: rgba(224,98,107,.12); color: #e0626b; }
        .pill-neutral { background: var(--surface-raised); color: var(--muted); border: 1px solid var(--border); }

        .dashboard-section-gap { height: 14px; }
        .dashboard-panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }
        .dashboard-panel-head {
            min-height: 78px;
            padding: 17px 24px 15px;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 24px;
            border-bottom: 1px solid var(--border);
        }
        .dashboard-panel-title { color: var(--text); font-size: 17px; font-weight: 700; line-height: 1.25; }
        .dashboard-panel-subtitle { color: var(--muted); font-size: 13px; margin-top: 3px; }
        .dashboard-panel-link { color: var(--accent); font-size: 13px; text-decoration: none; padding-top: 7px; white-space: nowrap; }
        .dashboard-panel-link:hover { color: #9187ff; }

        .pipeline-panel { padding: 25px 24px 22px; }
        .pipeline-head { display: flex; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
        .pipeline-title { font-size: 18px; font-weight: 700; color: var(--text); }
        .pipeline-subtitle { color: var(--muted); font-size: 13px; margin-top: 3px; }
        .pipeline-live { color: #8da3d2; font-size: 12px; padding-top: 8px; }
        .pipeline-flow { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 12px; }
        .pipeline-stage {
            width: 190px;
            min-height: 68px;
            padding: 13px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            background: #181e2b;
            border: 1px solid #2b3242;
            border-radius: 8px;
        }
        .pipeline-icon {
            width: 38px;
            height: 38px;
            flex: 0 0 38px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            background: #567dff;
            color: #fff;
            font-size: 19px;
            font-weight: 500;
        }
        .pipeline-stage-name { color: #fff; font-size: 14px; font-weight: 700; }
        .pipeline-stage-number { color: var(--muted); font-size: 11px; margin-top: 2px; }
        .pipeline-arrow { color: #9aa6bc; font-size: 22px; font-weight: 300; }

        .document-row {
            min-height: 72px;
            padding: 13px 24px;
            display: grid;
            grid-template-columns: 44px minmax(0, 1fr) auto;
            align-items: center;
            gap: 14px;
            border-bottom: 1px solid var(--border);
        }
        .document-row:last-child, .question-row:last-child { border-bottom: 0; }
        .document-icon {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            border: 1px solid #293143;
            background: #1c2333;
            color: var(--accent);
            font-size: 18px;
        }
        .document-name { color: var(--text); font-size: 14px; font-weight: 700; overflow-wrap: anywhere; }
        .document-meta { color: var(--muted); font-size: 11px; margin-top: 3px; }
        .status-outline {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border: 1px solid #d6dce8;
            border-radius: 999px;
            color: #fff;
            font-size: 11px;
            line-height: 1;
        }
        .status-failed { border-color: rgba(255,70,88,.25); background: rgba(255,70,88,.1); color: var(--danger); }

        .question-row { min-height: 78px; padding: 14px 24px; border-bottom: 1px solid var(--border); }
        .question-text { color: var(--text); font-size: 14px; font-weight: 500; overflow-wrap: anywhere; }
        .question-meta { margin-top: 7px; display: flex; align-items: center; gap: 10px; color: var(--muted); font-size: 11px; }
        .question-time { margin-left: auto; color: var(--muted); font-size: 11px; }
        .answered-badge { padding: 3px 8px; border: 1px solid #8490a6; border-radius: 5px; color: var(--muted); }

        .index-health {
            min-height: 88px;
            padding: 17px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
        }
        .index-health-main { display: flex; align-items: center; gap: 15px; min-width: 0; }
        .index-health-icon {
            width: 44px;
            height: 44px;
            flex: 0 0 44px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            background: #567dff;
            color: #fff;
            font-size: 20px;
        }
        .index-health-title { color: var(--text); font-size: 15px; font-weight: 700; }
        .index-health-meta { color: var(--muted); font-size: 12px; margin-top: 3px; }
        .backend-link {
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid #2c3445;
            background: #1a202d;
            color: #fff;
            font-size: 13px;
            text-decoration: none;
            white-space: nowrap;
        }
        .backend-link:hover { border-color: var(--accent); color: #fff; }

        .source-card { padding: 14px 16px; border-radius: 8px; background: #11151c; border: 1px solid var(--border); margin-bottom: 10px; }
        .source-card-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
        .source-title { font-weight: 600; color: var(--text); font-size: 14px; }
        .source-meta { color: var(--accent); font-size: 12px; font-weight: 500; }
        .source-preview, .small-muted { color: var(--muted); font-size: 13.5px; line-height: 1.55; }
        .faint { color: var(--faint); font-size: 12.5px; }
        .empty-state { text-align: center; padding: 48px 24px; border-radius: 8px; background: #11151c; border: 1px dashed var(--border); color: var(--muted); }
        .empty-state-title { color: var(--text); font-size: 15px; font-weight: 600; margin-bottom: 6px; }

        .stButton > button { border-radius: 7px; border: 1px solid var(--border); background: var(--surface-raised); color: var(--text); }
        textarea, input, .stTextInput input, .stSelectbox div[data-baseweb="select"] { border-radius: 7px !important; }
        div[data-testid="stChatMessage"], div[data-testid="stExpander"] { border-radius: 8px; background: #11151c; border: 1px solid var(--border) !important; }

        /* Chat page */
        .st-key-chat_simple_header {
            padding: 4px 0 25px;
            margin-bottom: 18px;
        }
        .chat-title-block.upload-page-header { margin-bottom: 0; }
        .chat-header-capabilities.upload-capability-row {
            margin-top: 18px;
            padding-bottom: 0;
            border: 0 !important;
        }
        .chat-single-divider {
            display: none !important;
        }
        .chat-simple-title {
            color: var(--text);
            font-size: 30px;
            font-weight: 750;
            line-height: 1.25;
        }
        .chat-simple-subtitle {
            margin-top: 24px;
            color: var(--muted);
            font-size: 14px;
            line-height: 1.55;
        }
        .chat-capability-row {
            display: flex;
            flex-wrap: wrap;
            gap: 9px;
            margin-top: 18px;
        }
        .chat-capability-row span {
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 7px;
            background: #1a2030;
            color: var(--muted);
            font-size: 11px;
            font-weight: 600;
        }
        .st-key-chat_simple_header .stButton > button {
            min-height: 44px;
            border-radius: 8px;
            background: #181e2a;
            font-size: 13px;
        }
        .st-key-chat_header {
            min-height: 196px;
            padding: 30px 36px 24px;
            margin-bottom: 20px;
            border: 0 !important;
            border-radius: 8px;
            background: transparent;
            box-shadow: none !important;
        }
        .st-key-chat_header::before,
        .st-key-chat_header::after,
        .st-key-chat_simple_header::before,
        .st-key-chat_simple_header::after,
        .st-key-chat_shell::before,
        .st-key-chat_shell::after {
            display: none !important;
            content: none !important;
        }
        .st-key-chat_header hr,
        .st-key-chat_simple_header hr,
        .st-key-chat_shell hr,
        .st-key-chat_header [data-testid="stDivider"],
        .st-key-chat_simple_header [data-testid="stDivider"],
        .st-key-chat_shell [data-testid="stDivider"] {
            display: none !important;
            border: 0 !important;
        }
        .st-key-chat_header [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-chat_simple_header [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-chat_shell [data-testid="stVerticalBlockBorderWrapper"] {
            border: 0 !important;
            box-shadow: none !important;
        }
        .chat-page-title { color: var(--text); font-size: 25px; font-weight: 700; line-height: 1.25; }
        .chat-page-subtitle {
            color: var(--muted);
            font-size: 14px;
            margin-top: 18px;
            margin-bottom: 0;
        }
        .st-key-chat_header div[data-testid="stPills"] {
            margin-top: 18px;
            padding-top: 12px;
        }
        .st-key-chat_header div[data-testid="stPills"] [role="listbox"],
        .st-key-chat_header div[data-testid="stPills"] [role="radiogroup"] {
            gap: 10px;
        }
        .st-key-chat_header div[data-testid="stPills"] button {
            min-height: 38px;
            padding: 7px 16px;
            border: 1px solid var(--border);
            border-radius: 999px;
            background: transparent;
            color: var(--muted);
            font-size: 13px;
            font-weight: 600;
        }
        .st-key-chat_header div[data-testid="stPills"] button[aria-pressed="true"] {
            border-color: #6475ff;
            background: #6475ff;
            color: #fff;
        }
        .st-key-chat_header .stButton > button {
            min-height: 44px;
            border-radius: 8px;
            background: #181e2a;
            font-size: 14px;
        }

        .st-key-chat_shell {
            padding: 10px 0 14px;
            margin-bottom: 20px;
            border: 0 !important;
            border-radius: 0;
            background: transparent;
            overflow: hidden;
        }
        .st-key-chat_conversation {
            min-height: 240px;
            padding: 8px 8px 24px;
        }
        .st-key-chat_conversation div[data-testid="stChatMessage"] {
            margin: 8px 0 18px;
            padding: 8px 0;
            border: 0 !important;
            background: transparent;
        }
        .chat-user-row {
            width: 100%;
            display: flex;
            justify-content: flex-end;
            padding: 4px 0 18px;
        }
        .chat-user-bubble {
            width: fit-content;
            max-width: 72%;
            padding: 13px 20px;
            border-radius: 24px 8px 24px 24px;
            background: #5f78ff;
            color: #fff;
            font-size: 14px;
            line-height: 1.55;
            text-align: left;
            overflow-wrap: anywhere;
        }
        .st-key-chat_conversation div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
            color: var(--text);
            font-size: 15px;
            line-height: 1.7;
        }
        .st-key-chat_conversation [data-testid="stChatMessageAvatarAssistant"] {
            width: 42px;
            height: 42px;
            border-radius: 8px;
            background: #5f78ff;
            color: #fff;
        }
        .assistant-byline { color: var(--muted); font-size: 12px; margin: 1px 0 8px; }
        .assistant-generating-row {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 12px 0 22px;
        }
        .assistant-generating-icon {
            width: 42px;
            height: 42px;
            flex: 0 0 42px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            background: #5f78ff;
            color: #fff;
            font-size: 19px;
            animation: assistant-icon-pulse 1.8s ease-in-out infinite;
        }
        .assistant-generating-label { color: var(--text); font-size: 13px; font-weight: 650; }
        .assistant-generating-stages { display: flex; gap: 10px; margin-top: 7px; }
        .assistant-generating-stages span {
            color: var(--faint);
            font-size: 10px;
            animation: generating-stage 3s ease-in-out infinite;
        }
        .assistant-generating-stages span:nth-child(2) { animation-delay: 1s; }
        .assistant-generating-stages span:nth-child(3) { animation-delay: 2s; }
        .assistant-generating-dots { display: flex; gap: 6px; margin-top: 8px; }
        .assistant-generating-dots span {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: #7568ff;
            animation: generating-pulse 1.2s ease-in-out infinite;
        }
        .assistant-generating-dots span:nth-child(2) { animation-delay: .15s; }
        .assistant-generating-dots span:nth-child(3) { animation-delay: .3s; }
        @keyframes generating-pulse {
            0%, 60%, 100% { opacity: .35; transform: translateY(0); }
            30% { opacity: 1; transform: translateY(-2px); }
        }
        @keyframes generating-stage {
            0%, 30%, 100% { color: var(--faint); }
            12%, 22% { color: #9187ff; }
        }
        @keyframes assistant-icon-pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.06); }
        }
        .st-key-chat_conversation .stButton > button,
        .st-key-chat_conversation .stDownloadButton > button {
            width: 100%;
            min-height: 34px;
            padding: 5px 8px;
            border: 1px solid #2b3242;
            border-radius: 7px;
            background: #151b27;
            color: var(--muted);
            font-size: 11px;
            white-space: nowrap;
        }
        .st-key-chat_conversation .stButton > button p,
        .st-key-chat_conversation .stDownloadButton > button p,
        .st-key-chat_conversation .stButton > button span,
        .st-key-chat_conversation .stDownloadButton > button span {
            white-space: nowrap !important;
            word-break: keep-all !important;
            overflow-wrap: normal !important;
        }
        .st-key-chat_conversation .stButton > button:hover,
        .st-key-chat_conversation .stDownloadButton > button:hover {
            color: var(--text);
            background: #181e2a;
        }
        .chat-welcome { padding: 52px 20px; text-align: center; color: var(--muted); }
        .chat-welcome-icon {
            width: 44px;
            height: 44px;
            display: grid;
            place-items: center;
            margin: 0 auto 12px;
            border-radius: 8px;
            background: #5f78ff;
            color: #fff;
            font-size: 20px;
        }
        .chat-welcome-title { color: var(--text); font-size: 16px; font-weight: 700; }
        .chat-welcome-copy { font-size: 13px; margin-top: 4px; }

        .st-key-chat_composer {
            padding: 6px 10px 6px 16px !important;
            border: 1px solid #2d3546 !important;
            border-radius: 30px !important;
            background: #0f1420 !important;
        }
        .st-key-chat_composer div[data-baseweb="input"] {
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        .st-key-chat_composer input {
            min-height: 44px;
            padding-left: 4px;
            background: transparent !important;
            color: var(--text) !important;
            font-size: 14px;
        }
        .st-key-chat_composer div[data-baseweb="select"] > div {
            min-height: 42px;
            border: 1px solid #2b3242;
            border-radius: 8px;
            background: #181e2b;
            color: var(--text);
            font-size: 11px;
        }
        .st-key-chat_composer .stFormSubmitButton > button {
            min-height: 46px;
            border: 0;
            border-radius: 18px;
            background: #5f78ff;
            color: #fff;
            font-size: 14px;
            font-weight: 700;
        }
        .st-key-chat_composer .stFormSubmitButton > button:hover {
            background: #7187ff;
            color: #fff;
        }
        .composer-attach-link {
            width: 38px;
            height: 38px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            color: #9aa6bc !important;
            font-size: 18px;
            line-height: 1;
            text-decoration: none !important;
        }
        .composer-attach-link:hover { background: #1c2333; color: #fff !important; }
        .chat-input-meta { color: var(--faint); font-size: 11px; margin: 8px 5px 0; }
        .chat-input-shortcut { color: var(--faint); font-size: 11px; margin: 8px 5px 0; text-align: right; }

        .chat-detail-panel, .st-key-chat_evidence_panel {
            padding: 25px 29px;
            margin-top: 18px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .chat-panel-head { display: flex; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
        .chat-panel-title { color: var(--text); font-size: 17px; font-weight: 700; }
        .chat-panel-subtitle { color: var(--muted); font-size: 12px; margin-top: 4px; }
        .chat-panel-count { color: var(--muted); font-size: 12px; padding-top: 3px; }
        .retrieval-row {
            min-height: 36px;
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
            gap: 18px;
            color: var(--muted);
            font-size: 13px;
        }
        .retrieval-value { color: var(--text); font-weight: 700; text-align: right; }
        .retrieval-label-icon { display: inline-block; width: 27px; color: #8c98ad; font-size: 16px; }
        .st-key-chat_evidence_panel div[data-testid="stExpander"] {
            margin-top: 12px;
            border: 1px solid #2b3242 !important;
            border-radius: 8px !important;
            background: #181e2b !important;
            overflow: hidden;
        }
        .st-key-chat_evidence_panel div[data-testid="stExpander"] summary {
            min-height: 58px;
            padding: 10px 14px;
            color: var(--text);
            font-size: 13px;
            font-weight: 700;
        }
        .st-key-chat_evidence_panel div[data-testid="stExpander"] summary:hover { color: var(--text); }
        .st-key-chat_evidence_panel div[data-testid="stExpander"]:first-of-type {
            border-color: rgba(117,104,255,.5) !important;
        }
        .evidence-card-detail-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            color: var(--muted);
            font-size: 11px;
            margin-bottom: 10px;
        }
        .evidence-expanded-meta { color: var(--muted); font-size: 11px; margin-bottom: 10px; }
        .evidence-expanded-score {
            display: inline-flex;
            padding: 3px 8px;
            margin-left: 8px;
            border: 1px solid #8490a6;
            border-radius: 5px;
        }
        .evidence-expanded-preview { color: var(--muted); font-size: 12px; line-height: 1.65; padding-bottom: 8px; }

        /* Upload page */
        .upload-page-header { margin-bottom: 26px; }
        .upload-page-header h1 {
            margin: 0;
            color: var(--text);
            font-size: 30px;
            font-weight: 700;
            line-height: 1.25;
        }
        .upload-page-header p {
            margin: 11px 0 0;
            color: var(--muted);
            font-size: 15px;
            line-height: 1.55;
        }
        .upload-capability-row { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 18px; padding-bottom: 24px; border-bottom: 1px solid var(--border); }
        .st-key-chat_simple_header,
        .st-key-chat_shell,
        .chat-header-capabilities {
            border: 0 !important;
            border-top: 0 !important;
            border-bottom: 0 !important;
        }
        .upload-capability-row span {
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 7px;
            background: #1a2030;
            color: var(--muted);
            font-size: 11px;
            font-weight: 600;
        }
        .compact-upload-label { color: var(--text); font-size: 13px; font-weight: 500; margin: 0 0 9px; }
        .st-key-compact_upload {
            width: 100%;
            padding: 10px 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .st-key-compact_upload [data-testid="stFileUploader"] { width: 100%; max-width: none; margin: 0; }
        .st-key-compact_upload [data-testid="stFileUploaderDropzone"] {
            width: 100%;
            min-height: 62px;
            padding: 8px 2px;
            justify-content: flex-start;
            gap: 18px;
            border: 0;
            background: transparent;
        }
        .st-key-compact_upload [data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
        .st-key-compact_upload [data-testid="stFileUploaderDropzone"]::after {
            content: "200MB per file · TXT, PDF, DOCX, CSV, MD";
            color: var(--muted);
            font-size: 13px;
        }
        .st-key-compact_upload [data-testid="stFileUploaderDropzone"] button,
        .st-key-compact_upload [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] {
            min-width: 112px;
            min-height: 42px;
            padding: 8px 15px;
            border: 1px solid #384154;
            border-radius: 7px;
            background: #181e2b;
            color: #fff;
            font-size: 13px;
            font-weight: 700;
        }
        .st-key-compact_upload [data-testid="stFileUploaderDropzone"] button::after,
        .st-key-compact_upload [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"]::after {
            content: none;
        }
        .st-key-compact_upload [data-testid="stFileUploaderFile"] { padding: 6px 10px; }
        .st-key-compact_upload [data-testid="stFileUploaderFile"] button::after { content: none; }

        .supported-types-panel { margin-top: 26px; padding: 25px 0 8px; border-top: 1px solid var(--border); }
        .supported-types-title { color: var(--text); font-size: 18px; font-weight: 700; }
        .supported-types-row { display: grid; grid-template-columns: repeat(5, 1fr); margin-top: 20px; text-align: center; }
        .supported-types-row span { color: var(--text); font-size: 12px; font-weight: 700; }
        .st-key-upload_zone {
            padding: 46px 58px 28px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .upload-zone-intro { text-align: center; }
        .upload-zone-icon {
            width: 62px;
            height: 62px;
            display: grid;
            place-items: center;
            margin: 0 auto 22px;
            border-radius: 8px;
            background: #567dff;
            color: #fff;
            font-size: 30px;
        }
        .upload-zone-title { color: var(--text); font-size: 19px; font-weight: 700; }
        .upload-zone-copy { color: var(--muted); font-size: 13px; margin-top: 7px; }
        .upload-type-row { display: flex; justify-content: center; gap: 7px; margin-top: 19px; }
        .upload-type-row span {
            padding: 5px 10px;
            border: 1px solid var(--border);
            border-radius: 999px;
            background: #1a2030;
            color: var(--muted);
            font-size: 10px;
        }
        .st-key-upload_zone [data-testid="stFileUploader"] { max-width: 620px; margin: 22px auto 0; }
        .st-key-upload_zone [data-testid="stFileUploaderDropzone"] {
            min-height: 68px;
            padding: 10px 14px;
            justify-content: center;
            border: 1px dashed #374055;
            border-radius: 8px;
            background: #101520;
        }
        .st-key-upload_zone [data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
        .st-key-upload_zone [data-testid="stFileUploaderDropzone"] button {
            border: 0;
            background: #5f78ff;
            color: #fff;
            font-weight: 700;
            font-size: 0;
        }
        .st-key-upload_zone [data-testid="stFileUploaderDropzone"] button::after {
            content: "⇧  Choose files";
            font-size: 13px;
        }
        .st-key-upload_zone .stButton > button:disabled {
            opacity: .65;
            border-color: var(--border);
            background: #181e2b;
            color: var(--muted);
        }
        .st-key-selected_upload {
            padding: 15px 18px;
            margin-top: 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .selected-file-name { color: var(--text); font-size: 14px; font-weight: 700; overflow-wrap: anywhere; }
        .selected-file-meta { color: var(--muted); font-size: 11px; margin-top: 4px; }

        .upload-timeline-panel {
            padding: 26px 30px 22px;
            margin-top: 18px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .upload-timeline-head { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 20px; }
        .upload-timeline-title { color: var(--text); font-size: 18px; font-weight: 700; }
        .upload-timeline-subtitle { color: var(--muted); font-size: 13px; margin-top: 4px; }
        .upload-timeline-status { color: var(--text); font-size: 12px; padding-top: 6px; }
        .upload-step {
            position: relative;
            min-height: 66px;
            display: grid;
            grid-template-columns: 44px minmax(0, 1fr);
            gap: 14px;
        }
        .upload-step:not(:last-child)::after {
            content: "";
            position: absolute;
            left: 21px;
            top: 40px;
            bottom: 0;
            width: 1px;
            background: #30384a;
        }
        .upload-step-icon {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border: 2px solid #2c3445;
            border-radius: 999px;
            background: #1a2030;
            color: #8d98ad;
            font-size: 16px;
            font-weight: 700;
            z-index: 1;
        }
        .upload-step-complete .upload-step-icon { border-color: #e5e9f1; color: #fff; }
        .upload-step-running .upload-step-icon { border-color: #7568ff; background: #567dff; color: #fff; }
        .upload-step-failed .upload-step-icon { border-color: var(--danger); color: var(--danger); }
        .upload-step-copy { padding-top: 3px; }
        .upload-step-name { color: var(--text); font-size: 14px; font-weight: 700; }
        .upload-step-detail { color: var(--muted); font-size: 12px; margin-top: 3px; }
        .upload-step-state {
            display: inline-flex;
            margin-left: 8px;
            padding: 3px 7px;
            border-radius: 5px;
            background: rgba(108,123,255,.12);
            color: #8d82ff;
            font-size: 10px;
            font-weight: 500;
        }

        .upload-success-panel {
            padding: 22px 26px;
            margin-top: 18px;
            display: grid;
            grid-template-columns: 58px minmax(0, 1fr) auto;
            align-items: center;
            gap: 18px;
            border: 1px solid #263a3e;
            border-radius: 8px;
            background: #15242a;
        }
        .upload-success-icon {
            width: 54px;
            height: 54px;
            display: grid;
            place-items: center;
            border: 1px solid #f1f4fa;
            border-radius: 8px;
            color: #fff;
            font-size: 23px;
        }
        .upload-success-title { color: var(--text); font-size: 16px; font-weight: 700; }
        .upload-success-subtitle { color: var(--muted); font-size: 12px; margin-top: 4px; }
        .upload-success-stats { display: grid; grid-template-columns: repeat(4, minmax(110px, 1fr)); gap: 10px; margin-top: 13px; }
        .upload-success-stat { padding: 10px 13px; border: 1px solid #304047; border-radius: 8px; background: #18242b; min-width: 0; }
        .upload-success-label { color: var(--muted); font-size: 9px; text-transform: uppercase; }
        .upload-success-value { color: var(--text); font-size: 13px; font-weight: 700; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .upload-documents-link {
            padding: 11px 15px;
            border: 1px solid #304047;
            border-radius: 8px;
            background: #18242b;
            color: #fff;
            font-size: 13px;
            font-weight: 700;
            text-decoration: none;
            white-space: nowrap;
        }

        /* Documents page */
        .documents-section-gap { height: 20px; }
        .st-key-document_filters {
            padding: 14px 16px 4px;
            margin-top: 18px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .documents-count { color: var(--muted); font-size: 11px; margin: 10px 2px 8px; }
        .st-key-documents_table {
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
            overflow: hidden;
        }
        .st-key-documents_table_header {
            padding: 13px 20px 11px;
            border-bottom: 1px solid var(--border);
        }
        .document-column-label { color: var(--muted); font-size: 10px; font-weight: 600; letter-spacing: .35px; }
        [class*="st-key-document_row_"] {
            padding: 13px 20px;
            border-bottom: 1px solid var(--border);
            background: var(--surface);
        }
        [class*="st-key-document_row_"]:last-child { border-bottom: 0; }
        .document-table-file { display: flex; align-items: center; gap: 13px; min-width: 0; }
        .document-table-icon {
            width: 42px;
            height: 42px;
            flex: 0 0 42px;
            display: grid;
            place-items: center;
            border: 1px solid #293143;
            border-radius: 8px;
            background: #1c2333;
            color: var(--accent);
            font-size: 18px;
        }
        .document-table-file-copy { min-width: 0; }
        .document-table-name {
            max-width: 300px;
            color: var(--text);
            font-size: 13px;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .document-table-id { color: var(--muted); font-size: 10px; margin-top: 3px; }
        .document-type-badge {
            display: inline-flex;
            padding: 4px 9px;
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--text);
            font-size: 10px;
            line-height: 1;
        }
        .type-pdf { border-color: rgba(255,70,88,.22); background: rgba(255,70,88,.09); color: #ff5263; }
        .type-md { border-color: rgba(70,130,255,.28); background: rgba(70,130,255,.1); color: #6d9aff; }
        .type-docx { border-color: rgba(117,104,255,.3); background: rgba(117,104,255,.1); color: #9388ff; }
        .type-csv { border-color: #d8deea; color: #fff; }
        .type-txt { border-color: rgba(63,185,127,.3); background: rgba(63,185,127,.1); color: #5fce93; }
        .document-table-status {
            display: inline-flex;
            padding: 5px 10px;
            border: 1px solid #d8deea;
            border-radius: 999px;
            color: #fff;
            font-size: 11px;
            line-height: 1;
        }
        .document-table-status.status-processing { border-color: #d8deea; color: #fff; }
        .document-table-status.status-failed { border-color: rgba(255,70,88,.25); background: rgba(255,70,88,.1); color: #ff4658; }
        .document-chunk-count { color: var(--text); font-size: 13px; }
        .document-upload-date { color: var(--muted); font-size: 12px; white-space: nowrap; }
        [class*="st-key-document_row_"] .stButton > button,
        [class*="st-key-document_row_"] .stDownloadButton > button,
        [class*="st-key-document_row_"] div[data-testid="stPopover"] > button {
            width: 29px;
            min-width: 29px;
            min-height: 29px;
            padding: 3px;
            border: 0;
            background: transparent;
            color: #8792a6;
        }
        [class*="st-key-document_row_"] .stButton > button:hover,
        [class*="st-key-document_row_"] .stDownloadButton > button:hover,
        [class*="st-key-document_row_"] div[data-testid="stPopover"] > button:hover {
            background: #1c2333;
            color: #fff;
        }
        [class*="st-key-document_viewer_"] {
            padding: 20px;
            margin-top: 14px;
            border: 1px solid #343d52;
            border-radius: 8px;
            background: #101621;
        }
        .document-viewer-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
            margin-bottom: 13px;
        }
        .document-viewer-title { color: var(--text); font-size: 15px; font-weight: 700; }
        .document-viewer-subtitle {
            max-width: 680px;
            margin-top: 3px;
            color: var(--muted);
            font-size: 11px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .document-viewer-head > span {
            flex: 0 0 auto;
            padding: 5px 9px;
            border: 1px solid #3a455d;
            border-radius: 999px;
            color: #a9b9d7;
            font-size: 10px;
        }
        [class*="st-key-document_viewer_"] [data-testid="stMetric"] {
            min-height: 76px;
            padding: 11px 13px;
            border: 1px solid var(--border);
            border-radius: 7px;
            background: #151c29;
        }
        [class*="st-key-document_viewer_"] [data-testid="stMetricLabel"] { font-size: 10px; }
        [class*="st-key-document_viewer_"] [data-testid="stMetricValue"] { font-size: 17px; }
        [class*="st-key-document_viewer_"] [data-baseweb="tab-list"] { margin-top: 5px; }
        .indexed-content-scroll {
            max-height: 430px;
            overflow-y: auto;
            margin-top: 8px;
            padding: 5px 17px;
            border: 1px solid var(--border);
            border-radius: 7px;
            background: #0c111b;
            scrollbar-color: #3a455d transparent;
        }
        .indexed-content-chunk {
            padding: 15px 0 16px;
            border-bottom: 1px solid var(--border);
        }
        .indexed-content-chunk:last-child { border-bottom: 0; }
        .indexed-content-chunk > div {
            margin-bottom: 7px;
            color: #8392ae;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .indexed-content-chunk p {
            margin: 0;
            color: #d9e0ec;
            font-size: 12px;
            line-height: 1.7;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }
        [class*="st-key-document_viewer_"] details {
            border-color: var(--border);
            border-radius: 7px;
            background: #121925;
        }

        /* History page */
        .st-key-history_search {
            padding: 13px 16px 3px;
            margin-top: 18px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .history-count { color: var(--muted); font-size: 11px; margin: 10px 2px 8px; }
        [class*="st-key-history_card_"] {
            padding: 22px 26px 18px;
            margin-bottom: 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .history-card-icon {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            background: #567dff;
            color: #fff;
            font-size: 21px;
        }
        .history-meta {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 6px;
            color: var(--muted);
            font-size: 11px;
            line-height: 1.5;
        }
        .history-meta-dot { color: #596579; }
        .history-question {
            margin-top: 10px;
            color: var(--text);
            font-size: 16px;
            font-weight: 700;
            line-height: 1.45;
            overflow-wrap: anywhere;
        }
        .history-answer-preview {
            display: -webkit-box;
            margin-top: 11px;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.75;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
            overflow: hidden;
            overflow-wrap: anywhere;
        }
        .history-status-wrap { display: flex; justify-content: flex-end; }
        .history-status {
            display: inline-flex;
            padding: 5px 10px;
            border: 1px solid #8490a6;
            border-radius: 999px;
            color: var(--muted);
            font-size: 10px;
            line-height: 1;
        }
        .history-status-failed { border-color: rgba(255,70,88,.25); background: rgba(255,70,88,.1); color: #ff4658; }
        .history-status-pending { border-color: rgba(217,164,65,.3); color: #d9a441; }
        .history-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-left: 60px; }
        .history-tag {
            display: inline-flex;
            padding: 4px 9px;
            border: 1px solid var(--border);
            border-radius: 999px;
            background: #181e2b;
            color: var(--muted);
            font-size: 10px;
        }
        [class*="st-key-history_card_"] .stButton > button {
            float: right;
            min-height: 30px;
            padding: 3px 8px;
            border: 0;
            background: transparent;
            color: var(--accent);
            font-size: 11px;
            font-weight: 700;
        }
        [class*="st-key-history_card_"] .stButton > button:hover {
            background: #1c2333;
            color: #9187ff;
        }
        .history-expanded-divider { height: 1px; margin: 13px 0 16px; background: var(--border); }
        [class*="st-key-history_card_"] div[data-testid="stMarkdownContainer"] p {
            color: var(--muted);
            font-size: 13px;
            line-height: 1.75;
        }

        /* Analytics page */
        .st-key-analytics_filters {
            padding: 13px 16px 4px;
            margin-bottom: 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .analytics-filter-summary {
            min-height: 38px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-top: 25px;
            color: var(--muted);
            font-size: 11px;
        }
        .analytics-health-strip {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            margin: 16px 0;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
            overflow: hidden;
        }
        .analytics-health-strip > div {
            min-width: 0;
            padding: 14px 16px;
            border-right: 1px solid var(--border);
        }
        .analytics-health-strip > div:last-child { border-right: 0; }
        .analytics-health-strip span { display: block; color: var(--muted); font-size: 10px; }
        .analytics-health-strip strong {
            display: block;
            margin-top: 5px;
            color: var(--text);
            font-size: 15px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .st-key-analytics_latency_chart,
        .st-key-analytics_volume_chart,
        .st-key-analytics_distribution_chart,
        .st-key-analytics_query_status,
        .st-key-analytics_document_status,
        .st-key-analytics_document_types,
        .st-key-analytics_top_questions,
        .st-key-analytics_recent_queries {
            min-height: 310px;
            padding: 18px 20px 12px;
            margin-bottom: 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .st-key-analytics_distribution_chart,
        .st-key-analytics_query_status,
        .st-key-analytics_document_status,
        .st-key-analytics_document_types { min-height: 290px; }
        .st-key-analytics_top_questions,
        .st-key-analytics_recent_queries { min-height: 360px; }
        .analytics-panel-title { color: var(--text); font-size: 15px; font-weight: 700; }
        .analytics-panel-subtitle { color: var(--muted); font-size: 11px; margin: 3px 0 12px; }
        .analytics-question-row {
            min-height: 42px;
            display: grid;
            grid-template-columns: 24px minmax(0, 1fr) auto;
            align-items: center;
            gap: 9px;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }
        .analytics-question-row:last-child { border-bottom: 0; }
        .analytics-question-rank {
            width: 22px;
            height: 22px;
            display: grid;
            place-items: center;
            border-radius: 6px;
            background: #1c2333;
            color: var(--accent);
            font-size: 10px;
            font-weight: 700;
        }
        .analytics-question-text {
            color: var(--muted);
            font-size: 11px;
            line-height: 1.45;
            overflow-wrap: anywhere;
        }
        .analytics-question-row strong { color: var(--text); font-size: 11px; }

        /* Settings page */
        .settings-section-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 14px;
        }
        .settings-section-title { color: var(--text); font-size: 18px; font-weight: 700; }
        .settings-section-subtitle { color: var(--muted); font-size: 13px; margin-top: 4px; }
        .settings-overall-health { color: var(--muted); font-size: 11px; padding-top: 8px; }
        .settings-overall-health.is-healthy { color: #58c98d; }
        .settings-overall-health.is-offline { color: #ff5263; }
        .settings-environment-card {
            position: relative;
            min-height: 154px;
            padding: 21px 22px;
            margin-bottom: 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .settings-card-icon {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border: 1px solid #293143;
            border-radius: 8px;
            background: #1c2333;
            color: var(--accent);
            font-size: 19px;
        }
        .settings-card-badge {
            position: absolute;
            top: 31px;
            right: 22px;
            padding: 4px 10px;
            border: 1px solid #d8deea;
            border-radius: 999px;
            color: #fff;
            font-size: 10px;
        }
        .settings-card-badge-danger { border-color: rgba(255,70,88,.3); color: #ff5263; }
        .settings-card-label { margin-top: 20px; color: var(--muted); font-size: 10px; font-weight: 600; text-transform: uppercase; }
        .settings-card-value {
            margin-top: 6px;
            color: var(--text);
            font-size: 16px;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .st-key-settings_troubleshooting {
            margin-top: 18px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
            overflow: hidden;
        }
        .settings-troubleshooting-head {
            min-height: 92px;
            padding: 20px 25px;
            display: grid;
            grid-template-columns: 48px minmax(0, 1fr) auto;
            align-items: center;
            gap: 16px;
            border-bottom: 1px solid var(--border);
        }
        .settings-troubleshooting-icon {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            background: #567dff;
            color: #fff;
            font-size: 19px;
        }
        .settings-troubleshooting-title { color: var(--text); font-size: 16px; font-weight: 700; }
        .settings-troubleshooting-subtitle { color: var(--muted); font-size: 11px; margin-top: 3px; }
        .settings-troubleshooting-head a { color: var(--accent); font-size: 11px; text-decoration: none; }
        [class*="st-key-settings_command_"] {
            min-height: 76px;
            padding: 13px 25px;
            border-bottom: 1px solid var(--border);
        }
        [class*="st-key-settings_command_"]:last-child { border-bottom: 0; }
        .settings-command-icon {
            width: 38px;
            height: 38px;
            display: grid;
            place-items: center;
            border: 1px solid #293143;
            border-radius: 8px;
            background: #1c2333;
            color: var(--accent);
            font-size: 13px;
        }
        .settings-command-title { color: var(--text); font-size: 13px; font-weight: 700; }
        .settings-command-description { color: var(--muted); font-size: 10px; margin-top: 3px; }
        .settings-command-code {
            padding: 11px 14px;
            border: 1px solid #2b3242;
            border-radius: 7px;
            background: #101520;
            color: var(--muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 11px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        [class*="st-key-settings_command_"] .stButton > button {
            width: 100%;
            min-width: 82px;
            min-height: 40px;
            padding: 8px 12px;
            border: 0;
            border-radius: 8px;
            background: #5f78ff;
            color: #fff;
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
            word-break: keep-all;
        }
        [class*="st-key-settings_command_"] .stButton > button p,
        [class*="st-key-settings_command_"] .stButton > button span {
            white-space: nowrap !important;
            word-break: keep-all !important;
        }
        [class*="st-key-settings_command_"] .stButton > button:hover { background: #7187ff; color: #fff; }
        .settings-health-summary {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin: 18px 0;
            padding: 21px 26px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
        }
        .settings-health-summary > div {
            display: grid;
            grid-template-columns: 48px minmax(0, 1fr);
            grid-template-rows: auto auto;
            column-gap: 13px;
            align-items: center;
        }
        .settings-health-icon {
            width: 44px;
            height: 44px;
            grid-row: 1 / 3;
            display: grid;
            place-items: center;
            border: 1px solid #d8deea;
            border-radius: 8px;
            color: #fff;
            font-size: 17px;
        }
        .settings-health-summary p { margin: 0; color: var(--muted); font-size: 10px; font-weight: 600; }
        .settings-health-summary strong { color: var(--text); font-size: 19px; line-height: 1.2; }

        @media (max-width: 900px) {
            .pipeline-panel { padding: 22px 18px; }
            .pipeline-stage { width: calc(50% - 26px); min-width: 180px; flex-grow: 1; }
            .dashboard-panel-head, .document-row, .question-row { padding-left: 18px; padding-right: 18px; }
        }
        @media (max-width: 640px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .pipeline-head, .index-health { align-items: flex-start; flex-direction: column; }
            .pipeline-live { padding-top: 0; }
            .pipeline-flow { display: grid; grid-template-columns: 1fr; }
            .pipeline-stage { width: 100%; min-width: 0; }
            .pipeline-arrow { text-align: center; transform: rotate(90deg); line-height: .7; }
            .dashboard-panel-head { min-height: 0; padding: 16px; }
            .dashboard-panel-title, .pipeline-title { font-size: 17px; }
            .dashboard-panel-subtitle, .pipeline-subtitle { font-size: 12px; }
            .document-row { grid-template-columns: 40px minmax(0, 1fr); padding: 13px 16px; gap: 11px; }
            .document-icon { width: 38px; height: 38px; }
            .document-status { grid-column: 2; }
            .question-row { padding: 13px 16px; }
            .question-meta { flex-wrap: wrap; }
            .question-time { width: 100%; margin-left: 0; }
            .index-health { padding: 17px 16px; }
            .backend-link { width: 100%; text-align: center; }
            .st-key-chat_header { min-height: 0; padding: 22px 18px 18px; }
            .chat-page-title { font-size: 21px; }
            .chat-page-subtitle { font-size: 12px; }
            .st-key-chat_shell { padding: 14px 12px 10px; }
            .st-key-chat_conversation { min-height: 190px; padding-left: 0; padding-right: 0; }
            .chat-user-bubble { max-width: 88%; }
            .st-key-chat_composer { padding-left: 8px !important; }
            .st-key-chat_composer .stFormSubmitButton > button { padding-left: 8px; padding-right: 8px; }
            .composer-attach-link { width: 32px; height: 32px; font-size: 16px; }
            .chat-detail-panel, .st-key-chat_evidence_panel { padding: 19px 16px; }
            .retrieval-row { grid-template-columns: 1fr; gap: 2px; padding: 6px 0; }
            .retrieval-value { padding-left: 27px; text-align: left; }
            .st-key-upload_zone { padding: 30px 18px 22px; }
            .upload-type-row { flex-wrap: wrap; }
            .upload-timeline-panel { padding: 21px 17px 18px; }
            .upload-success-panel { grid-template-columns: 48px minmax(0, 1fr); padding: 18px 16px; }
            .upload-success-icon { width: 46px; height: 46px; }
            .upload-success-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .upload-documents-link { grid-column: 1 / -1; text-align: center; }
            .st-key-compact_upload [data-testid="stFileUploaderDropzone"] { align-items: flex-start; flex-direction: column; gap: 8px; }
            .st-key-compact_upload [data-testid="stFileUploaderDropzone"]::after { font-size: 11px; }
            .supported-types-row { grid-template-columns: repeat(3, 1fr); row-gap: 18px; }
            .st-key-documents_table { overflow-x: auto; }
            .st-key-documents_table_header { min-width: 900px; }
            [class*="st-key-document_row_"] { min-width: 900px; padding-left: 14px; padding-right: 14px; }
            [class*="st-key-document_viewer_"] { min-width: 860px; padding: 16px; }
            [class*="st-key-history_card_"] { padding: 18px 16px 15px; }
            .history-card-icon { width: 36px; height: 36px; font-size: 17px; }
            .history-question { font-size: 14px; }
            .history-answer-preview { font-size: 12px; line-height: 1.7; }
            .history-status-wrap { justify-content: flex-start; }
            .history-tags { margin-left: 0; }
            .analytics-filter-summary { justify-content: flex-start; padding-top: 0; }
            .analytics-health-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .analytics-health-strip > div { border-bottom: 1px solid var(--border); }
            .analytics-health-strip > div:nth-child(2n) { border-right: 0; }
            .settings-section-head { flex-direction: column; gap: 4px; }
            .settings-environment-card { min-height: 138px; }
            .settings-troubleshooting-head { grid-template-columns: 42px minmax(0, 1fr); padding: 17px 15px; }
            .settings-troubleshooting-head a { grid-column: 2; }
            [class*="st-key-settings_command_"] { padding: 12px 15px; }
            .settings-command-code { white-space: normal; overflow-wrap: anywhere; }
            .settings-health-summary { grid-template-columns: 1fr; gap: 18px; padding: 18px; }
        }

        /* Final sidebar layout lock: all seven pages fit without scrolling. */
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] > div {
            overflow: hidden !important;
            scrollbar-width: none !important;
        }
        section[data-testid="stSidebar"] ::-webkit-scrollbar {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            position: fixed !important;
            top: 132px !important;
            bottom: auto !important;
            left: 0 !important;
            width: 300px !important;
            height: auto !important;
            max-height: none !important;
            padding: 8px 14px !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul {
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            gap: 2px !important;
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li {
            display: block !important;
            flex: 0 0 34px !important;
            width: 100% !important;
            height: 34px !important;
            min-height: 34px !important;
            max-height: 34px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
            box-sizing: border-box !important;
            width: 100% !important;
            height: 34px !important;
            min-height: 34px !important;
            max-height: 34px !important;
            padding: 4px 11px !important;
            border-radius: 7px !important;
            font-size: 12px !important;
            line-height: 1 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li a::before {
            width: 20px !important;
            height: 20px !important;
            flex-basis: 20px !important;
            font-size: 14px !important;
        }
        .sidebar-workspace-label { top: 112px !important; }
        .sidebar-environment-card { display: none !important; }

        /* Production RAG sidebar */
        section[data-testid="stSidebar"] {
            display: block !important;
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
            height: 100dvh !important;
            overflow: hidden !important;
            border-right: 1px solid #1d2331 !important;
            background: #050811 !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"]::before { display: none !important; }
        section[data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            height: 100dvh !important;
            max-height: 100dvh !important;
            overflow: hidden !important;
            background: #050811 !important;
            scrollbar-width: none !important;
        }
        section[data-testid="stSidebar"] ::-webkit-scrollbar { display: none !important; width: 0 !important; }
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] { display: none !important; }

        .sidebar-brand-panel {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            box-sizing: border-box !important;
            width: 300px !important;
            height: 184px !important;
            padding: 24px 20px 20px !important;
            border: 0 !important;
            border-bottom: 1px solid #171d2a !important;
            border-radius: 0 !important;
            background: #050811 !important;
            box-shadow: none !important;
            z-index: 20 !important;
        }
        .sidebar-brand-panel::before { display: none !important; }
        .sidebar-product-brand {
            display: grid !important;
            grid-template-columns: 60px minmax(0, 1fr) !important;
            gap: 18px !important;
            align-items: center !important;
        }
        .sidebar-product-mark {
            width: 60px !important;
            height: 60px !important;
            border: 0 !important;
            border-radius: 19px !important;
            background: linear-gradient(145deg, #846cff, #35a8ff) !important;
            color: #fff !important;
            box-shadow: 0 12px 28px rgba(77,116,255,.3) !important;
        }
        .sidebar-product-mark .material-symbols-rounded {
            color: #fff !important;
            font-size: 33px !important;
            line-height: 1 !important;
        }
        .sidebar-product-name {
            color: #fff !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            line-height: 1.25 !important;
        }
        .sidebar-product-subtitle {
            margin-top: 4px !important;
            color: #8ea0c7 !important;
            font-size: 12px !important;
            font-weight: 400 !important;
            letter-spacing: 0 !important;
            text-transform: none !important;
        }
        .sidebar-status-chips {
            position: absolute !important;
            left: 20px !important;
            right: 20px !important;
            bottom: 35px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
            margin: 0 !important;
        }
        .sidebar-health-chip,
        .sidebar-model-chip {
            min-height: 29px !important;
            padding: 5px 12px !important;
            border-radius: 999px !important;
            font-size: 11px !important;
            font-weight: 650 !important;
        }
        .sidebar-health-chip {
            border: 1px solid #d9deea !important;
            background: transparent !important;
            color: #fff !important;
        }
        .sidebar-health-chip::before { display: none !important; }
        .sidebar-model-chip {
            border: 1px solid #242b3b !important;
            background: #1a2030 !important;
            color: #8e9cba !important;
        }
        .sidebar-workspace-label {
            position: fixed !important;
            top: 201px !important;
            left: 29px !important;
            z-index: 20 !important;
            color: #7282a6 !important;
            font-size: 11px !important;
            font-weight: 500 !important;
            letter-spacing: .7px !important;
            text-transform: uppercase !important;
        }
        .sidebar-workspace-label::after { display: none !important; }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            position: fixed !important;
            top: 230px !important;
            bottom: 124px !important;
            left: 0 !important;
            box-sizing: border-box !important;
            width: 300px !important;
            height: auto !important;
            max-height: none !important;
            padding: 0 14px !important;
            overflow: hidden !important;
            z-index: 10 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] > div {
            height: 100% !important;
            max-height: none !important;
            overflow: hidden !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul {
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            gap: 4px !important;
            height: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li {
            display: block !important;
            width: 100% !important;
            height: 42px !important;
            min-height: 42px !important;
            max-height: 42px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
            box-sizing: border-box !important;
            width: 100% !important;
            height: 42px !important;
            min-height: 42px !important;
            max-height: 42px !important;
            gap: 11px !important;
            padding: 6px 15px !important;
            border: 1px solid transparent !important;
            border-radius: 10px !important;
            background: transparent !important;
            color: #98a7c5 !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            line-height: 1 !important;
            transform: none !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
            background: #101625 !important;
            color: #e9edf6 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
            border-color: transparent !important;
            background: #171d2c !important;
            color: #fff !important;
            font-weight: 650 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li a::before {
            width: 24px !important;
            height: 24px !important;
            flex: 0 0 24px !important;
            display: grid !important;
            place-items: center !important;
            border-radius: 0 !important;
            background: transparent !important;
            color: #8f9bb1 !important;
            font-size: 18px !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"]::before {
            color: #806cff !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"]::after {
            content: "" !important;
            width: 7px !important;
            height: 7px !important;
            margin-left: auto !important;
            border-radius: 50% !important;
            background: #806cff !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child a span { display: none !important; }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child a::after,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:first-child a[aria-current="page"]::after {
            content: "Dashboard" !important;
            width: auto !important;
            height: auto !important;
            margin-left: 0 !important;
            border-radius: 0 !important;
            background: transparent !important;
            color: inherit !important;
            font-size: 14px !important;
            font-weight: inherit !important;
        }

        .sidebar-environment-card {
            display: block !important;
            position: fixed !important;
            left: 18px !important;
            bottom: 12px !important;
            box-sizing: border-box !important;
            width: 264px !important;
            min-height: 98px !important;
            padding: 14px 17px !important;
            margin: 0 !important;
            border: 1px solid #222a3b !important;
            border-radius: 10px !important;
            background: #141a28 !important;
            box-shadow: none !important;
            z-index: 20 !important;
        }
        .sidebar-environment-label { color: #7988a8 !important; font-size: 11px !important; font-weight: 500 !important; letter-spacing: .5px !important; }
        .sidebar-environment-title { margin-top: 7px !important; color: #fff !important; font-size: 14px !important; font-weight: 650 !important; }
        .sidebar-environment-copy { margin-top: 4px !important; color: #8a99b8 !important; font-size: 11px !important; }

        @media (max-height: 760px) {
            .sidebar-brand-panel { height: 154px !important; padding-top: 16px !important; }
            .sidebar-product-mark { width: 52px !important; height: 52px !important; }
            .sidebar-product-brand { grid-template-columns: 52px minmax(0, 1fr) !important; gap: 14px !important; }
            .sidebar-status-chips { bottom: 26px !important; }
            .sidebar-workspace-label { top: 167px !important; }
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { top: 192px !important; bottom: 108px !important; }
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li,
            section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
                height: 42px !important;
                min-height: 42px !important;
                max-height: 42px !important;
            }
            .sidebar-environment-card { min-height: 80px !important; padding: 10px 16px !important; }
            .sidebar-environment-title { margin-top: 5px !important; }
        }

        /* Product top bar and safe page offset. */
        header[data-testid="stHeader"] {
            height: 68px !important;
            border-bottom: 1px solid #202737 !important;
            background: rgba(13,17,28,.98) !important;
            backdrop-filter: blur(12px);
            transition: transform .22s ease, opacity .18s ease;
        }
        header[data-testid="stHeader"] [data-testid="stToolbar"],
        header[data-testid="stHeader"] [data-testid="stHeaderActionElements"],
        header[data-testid="stHeader"] [data-testid="stMainMenu"],
        header[data-testid="stHeader"] [data-testid="stStatusWidget"],
        header[data-testid="stHeader"] .stDeployButton,
        header[data-testid="stHeader"] #MainMenu {
            display: none !important;
        }
        .app-topbar-context {
            position: fixed;
            top: 0;
            left: 300px;
            right: 0;
            box-sizing: border-box;
            height: 68px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 28px;
            padding: 0 30px;
            color: #aab5c9;
            z-index: 1000001;
            pointer-events: auto;
            transition: transform .22s ease, opacity .18s ease;
        }
        header[data-testid="stHeader"].rag-topbar-hidden,
        .app-topbar-context.rag-topbar-hidden {
            transform: translateY(-105%);
            opacity: 0;
            pointer-events: none;
        }
        .app-topbar-identity,
        .app-topbar-health,
        .app-topbar-runtime,
        .app-topbar-actions,
        .app-topbar-link {
            display: inline-flex;
            align-items: center;
        }
        .app-topbar-identity { gap: 9px; min-width: 0; }
        .app-topbar-icon {
            width: 30px;
            height: 30px;
            display: grid;
            place-items: center;
            border: 1px solid #2e3850;
            border-radius: 8px;
            background: #171e2c;
            color: #8178ff;
        }
        .app-topbar-icon .material-symbols-rounded { color: inherit; font-size: 18px; }
        .app-topbar-name { color: #f4f6fb; font-size: 14px; font-weight: 750; white-space: nowrap; }
        .app-topbar-separator { color: #3f4960; font-size: 14px; }
        .app-topbar-location {
            color: #8794ad;
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .app-topbar-health {
            flex: 0 0 auto;
            gap: 7px;
            padding: 5px 10px;
            border: 1px solid #2d374b;
            border-radius: 999px;
            background: #151c29;
            color: #98a7c1;
            font-size: 10px;
            font-weight: 600;
        }
        .app-topbar-runtime {
            flex: 0 0 auto;
            gap: 8px;
        }
        .app-topbar-model {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            border: 1px solid #30384a;
            border-radius: 999px;
            background: #171e2c;
            color: #aab5c9;
            font-size: 10px;
            font-weight: 650;
            white-space: nowrap;
        }
        .app-topbar-actions {
            flex: 1 1 auto;
            justify-content: space-evenly;
            gap: clamp(12px, 2vw, 38px);
        }
        .app-topbar-link {
            gap: 6px;
            min-height: 34px;
            padding: 0 9px;
            border: 1px solid transparent;
            border-radius: 7px;
            color: #9eabc1 !important;
            font-size: 11px;
            font-weight: 600;
            text-decoration: none !important;
            white-space: nowrap;
            transition: background .15s ease, border-color .15s ease, color .15s ease;
        }
        .app-topbar-link:hover {
            border-color: #2d374b;
            background: #171e2c;
            color: #fff !important;
        }
        .app-topbar-link .material-symbols-rounded { font-size: 17px; color: #8279ff; }
        .app-topbar-health-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #55d394;
            box-shadow: 0 0 0 3px rgba(85,211,148,.1);
        }
        .app-topbar-health.is-offline .app-topbar-health-dot {
            background: #ff5263;
            box-shadow: 0 0 0 3px rgba(255,82,99,.1);
        }
        .block-container {
            padding-top: 5.75rem !important;
        }
        .page-header,
        .page-eyebrow {
            position: relative;
            overflow: visible !important;
        }
        @media (max-width: 1260px) {
            .app-topbar-context { padding: 0 15px; gap: 14px; }
            .app-topbar-location, .app-topbar-link span:last-child { display: none; }
            .app-topbar-link { padding: 0 8px; }
        }
        @media (max-width: 900px) {
            .app-topbar-context { gap: 8px; }
            .app-topbar-actions { gap: 1px; }
        }
        @media (max-height: 600px) {
            .sidebar-brand-panel { height: 132px !important; padding: 12px 18px !important; }
            .sidebar-product-mark { width: 46px !important; height: 46px !important; border-radius: 14px !important; }
            .sidebar-product-mark .material-symbols-rounded { font-size: 27px !important; }
            .sidebar-product-brand { grid-template-columns: 46px minmax(0, 1fr) !important; gap: 12px !important; }
            .sidebar-product-name { font-size: 14px !important; }
            .sidebar-product-subtitle { font-size: 10px !important; }
            .sidebar-status-chips { bottom: 25px !important; }
            .sidebar-health-chip, .sidebar-model-chip { min-height: 24px !important; padding: 3px 9px !important; font-size: 9px !important; }
            .sidebar-workspace-label { top: 143px !important; }
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { top: 166px !important; bottom: 90px !important; }
            section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li,
            section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
                height: 35px !important;
                min-height: 35px !important;
                max-height: 35px !important;
            }
            .sidebar-environment-card { bottom: 8px !important; min-height: 70px !important; padding: 8px 14px !important; }
            .sidebar-environment-title { margin-top: 3px !important; font-size: 12px !important; }
            .sidebar-environment-copy { margin-top: 2px !important; font-size: 10px !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    model_label = os.getenv("MODEL_LABEL", "llama3.2")
    app_version = os.getenv("APP_VERSION", "v1.4.0")
    if "_sidebar_backend_healthy" not in st.session_state:
        try:
            from api_client import check_backend_health

            st.session_state._sidebar_backend_healthy = check_backend_health()[0]
        except Exception:
            st.session_state._sidebar_backend_healthy = False
    backend_healthy = bool(st.session_state._sidebar_backend_healthy)
    backend_label = "Backend Online" if backend_healthy else "Backend Offline"
    backend_class = "" if backend_healthy else " is-offline"

    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand-panel">
            <div class="sidebar-product-brand">
                <div class="sidebar-product-mark"><span class="material-symbols-rounded">hub</span></div>
                <div>
                    <div class="sidebar-product-name">Production Grade RAG System</div>
                    <div class="sidebar-product-subtitle">Hybrid Knowledge Platform</div>
                </div>
            </div>
            <div class="sidebar-status-chips">
                <span class="sidebar-health-chip{backend_class}">{_safe(backend_label)}</span>
                <span class="sidebar-model-chip">✦ {_safe(model_label)}</span>
            </div>
        </div>
        <div class="sidebar-workspace-label">Workspace</div>
        <div class="sidebar-environment-card">
            <div class="sidebar-environment-label">Environment</div>
            <div class="sidebar-environment-title">Local AI Workspace</div>
            <div class="sidebar-environment-copy">{_safe(app_version)} · ChromaDB</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="app-topbar-context">
            <div class="app-topbar-runtime">
                <span class="app-topbar-model"><span class="material-symbols-rounded">memory</span>{_safe(model_label)}</span>
            </div>
            <nav class="app-topbar-actions" aria-label="Quick navigation">
                <a class="app-topbar-link" href="Chat" target="_self"><span class="material-symbols-rounded">forum</span><span>Ask AI</span></a>
                <a class="app-topbar-link" href="Upload" target="_self"><span class="material-symbols-rounded">upload_file</span><span>Ingest</span></a>
                <a class="app-topbar-link" href="Documents" target="_self"><span class="material-symbols-rounded">database</span><span>Knowledge Base</span></a>
                <a class="app-topbar-link" href="Analytics" target="_self"><span class="material-symbols-rounded">monitoring</span><span>Analytics</span></a>
                <a class="app-topbar-link" href="Settings" target="_self"><span class="material-symbols-rounded">settings</span><span>Settings</span></a>
            </nav>
        </div>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        """
        <script>
        (() => {
            const parentWindow = window.parent;
            const documentRef = parentWindow.document;
            const scroller = documentRef.querySelector('[data-testid="stMain"]')
                || documentRef.querySelector('section.main');
            const topbar = documentRef.querySelector('.app-topbar-context');

            if (!scroller || !topbar) return;

            const header = documentRef.querySelector('header[data-testid="stHeader"]');
            if (scroller.__ragTopbarScrollHandler) {
                scroller.removeEventListener('scroll', scroller.__ragTopbarScrollHandler);
            }

            let framePending = false;
            const updateTopbar = () => {
                framePending = false;
                const isAwayFromTop = scroller.scrollTop > 10;
                topbar.classList.toggle('rag-topbar-hidden', isAwayFromTop);
                if (header) header.classList.toggle('rag-topbar-hidden', isAwayFromTop);
            };
            const handleScroll = () => {
                if (framePending) return;
                framePending = true;
                parentWindow.requestAnimationFrame(updateTopbar);
            };

            scroller.__ragTopbarScrollHandler = handleScroll;
            scroller.addEventListener('scroll', handleScroll, { passive: true });
            updateTopbar();

            const componentContainer = window.frameElement
                && window.frameElement.closest('[data-testid="stElementContainer"]');
            if (componentContainer) componentContainer.style.display = 'none';
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def page_header(eyebrow: str, title: str, subtitle: str, tags=None):
    tags = tags or []
    tag_html = "".join(f'<span class="tag">{_safe(tag)}</span>' for tag in tags)
    st.markdown(
        f'<div class="page-header"><div class="page-eyebrow">{_safe(eyebrow)}</div>'
        f'<h1 class="page-title">{_safe(title)}</h1><div class="page-subtitle">{_safe(subtitle)}</div>'
        f'<div class="tag-row">{tag_html}</div></div>',
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, badges=None):
    page_header("", title, subtitle, badges)


def metric_card(label: str, value, help_text: str = "", delta: str = None, delta_positive: bool = True):
    delta_html = ""
    if delta:
        css_class = "metric-delta-up" if delta_positive else "metric-delta-down"
        arrow = "↑" if delta_positive else "↓"
        delta_html = f'<div class="{css_class}">{arrow} {_safe(delta)}</div>'
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{_safe(label)}</div>'
        f'<div class="metric-value">{_safe(value)}</div><div class="metric-help">{_safe(help_text)}</div>'
        f'{delta_html}</div>',
        unsafe_allow_html=True,
    )


def status_pill(text: str, kind: str = "neutral"):
    return f'<span class="pill pill-{_safe(kind)}">{_safe(text)}</span>'


def dashboard_pipeline():
    stages = [
        ("⇧", "Upload", "Stage 1"),
        ("▱", "Parse", "Stage 2"),
        ("≡", "Chunk", "Stage 3"),
        ("✦", "Embed", "Stage 4"),
        ("⌕", "Retrieve", "Stage 5"),
        ("▣", "Generate Answer", "Stage 6"),
    ]
    flow = []
    for index, (icon, name, number) in enumerate(stages):
        flow.append(
            f'<div class="pipeline-stage"><div class="pipeline-icon">{icon}</div>'
            f'<div><div class="pipeline-stage-name">{name}</div>'
            f'<div class="pipeline-stage-number">{number}</div></div></div>'
        )
        if index < len(stages) - 1:
            flow.append('<div class="pipeline-arrow">→</div>')
    st.markdown(
        '<section class="dashboard-panel pipeline-panel">'
        '<div class="pipeline-head"><div><div class="pipeline-title">System Pipeline</div>'
        '<div class="pipeline-subtitle">End-to-end retrieval-augmented generation flow</div></div>'
        '<div class="pipeline-live">Real-time</div></div>'
        f'<div class="pipeline-flow">{"".join(flow)}</div></section>',
        unsafe_allow_html=True,
    )


def dashboard_recent_documents(documents):
    rows = []
    for document in documents:
        status_text, status_class = _document_status(document)
        rows.append(
            '<div class="document-row">'
            '<div class="document-icon">▤</div>'
            '<div><div class="document-name">{}</div><div class="document-meta">{} · {:,} chunks · {}</div></div>'
            '<div class="document-status"><span class="status-outline status-{}">{}</span></div></div>'.format(
                _safe(document.get("filename"), "Unknown file"),
                _safe(_document_type(document)),
                int(document.get("total_chunks") or 0),
                _relative_time(document.get("created_at")),
                status_class,
                status_text,
            )
        )
    st.markdown(
        '<section class="dashboard-panel"><div class="dashboard-panel-head"><div>'
        '<div class="dashboard-panel-title">Recent Documents</div>'
        '<div class="dashboard-panel-subtitle">Last 5 ingested into the knowledge base</div></div>'
        '<a class="dashboard-panel-link" href="#">View all&nbsp; →</a></div>'
        f'{"".join(rows)}</section>',
        unsafe_allow_html=True,
    )


def dashboard_recent_questions(history):
    rows = []
    for item in history:
        latency_ms = item.get("latency_ms")
        try:
            latency = f"{float(latency_ms) / 1000:.2f}s" if latency_ms is not None else "-"
        except (TypeError, ValueError):
            latency = _safe(latency_ms)
        status = str(item.get("status") or "answered").lower()
        status_text = "Answered" if status in {"success", "answered", "completed"} else status.title()
        rows.append(
            '<div class="question-row"><div class="question-text">{}</div>'
            '<div class="question-meta"><span>◔ {}</span><span class="answered-badge">{}</span>'
            '<span class="question-time">{}</span></div></div>'.format(
                _safe(item.get("question"), "No question"),
                latency,
                _safe(status_text),
                _relative_time(item.get("created_at")),
            )
        )
    st.markdown(
        '<section class="dashboard-panel"><div class="dashboard-panel-head"><div>'
        '<div class="dashboard-panel-title">Recent Questions</div>'
        '<div class="dashboard-panel-subtitle">Latest hybrid retrieval queries</div></div>'
        '<a class="dashboard-panel-link" href="#">History&nbsp; →</a></div>'
        f'{"".join(rows)}</section>',
        unsafe_allow_html=True,
    )


def dashboard_index_health(
    healthy: bool,
    vector_count: int,
    embedding_dimension: int,
    last_reindex,
    api_docs_url: str,
    offline_message: str = "",
):
    state = "healthy" if healthy else "offline"
    title = f"ChromaDB · BM25 hybrid index {state}"
    if healthy:
        meta = f"{int(vector_count or 0):,} vectors · {embedding_dimension}-dim embeddings · last reindex {_relative_time(last_reindex)}"
    else:
        meta = offline_message or "Backend is unavailable"
    st.markdown(
        '<section class="index-health"><div class="index-health-main"><div class="index-health-icon">▤</div>'
        f'<div><div class="index-health-title">{_safe(title)}</div><div class="index-health-meta">{_safe(meta)}</div></div></div>'
        f'<a class="backend-link" href="{_safe(api_docs_url)}" target="_blank">Manage backend&nbsp;&nbsp; →</a></section>',
        unsafe_allow_html=True,
    )


def chat_retrieval_panel(
    sources_found: int,
    max_sources: int,
    latency_ms,
    search_type: str,
    vector_db: str,
    model: str,
):
    try:
        latency_label = f"{float(latency_ms) / 1000:.2f}s"
    except (TypeError, ValueError):
        latency_label = "-"

    rows = [
        ("▤", "Sources found", f"{sources_found} / {max_sources}"),
        ("◔", "Latency", latency_label),
        ("⌕", "Search type", search_type),
        ("▤", "Vector DB", vector_db),
        ("▣", "Model", model),
    ]
    rows_html = "".join(
        '<div class="retrieval-row">'
        f'<div><span class="retrieval-label-icon">{icon}</span>{_safe(label)}</div>'
        f'<div class="retrieval-value">{_safe(value)}</div></div>'
        for icon, label, value in rows
    )
    st.markdown(
        '<section class="chat-detail-panel"><div class="chat-panel-head"><div>'
        '<div class="chat-panel-title">Retrieval Details</div>'
        '<div class="chat-panel-subtitle">Pipeline metadata for the last query</div>'
        f'</div></div>{rows_html}</section>',
        unsafe_allow_html=True,
    )


def chat_evidence_panel(sources):
    def source_score(source):
        value = source.get("score")
        if value is None:
            value = source.get("similarity_score")
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("-inf")

    source_list = sorted(sources or [], key=source_score, reverse=True)
    with st.container(key="chat_evidence_panel"):
        st.markdown(
            '<div class="chat-panel-head"><div>'
            '<div class="chat-panel-title">Evidence</div>'
            '<div class="chat-panel-subtitle">Top chunks retrieved for this answer</div></div>'
            f'<div class="chat-panel-count">{len(source_list)} sources</div></div>',
            unsafe_allow_html=True,
        )

        if not source_list:
            st.markdown(
                '<div class="evidence-expanded-preview">'
                'No source evidence was returned for this answer.</div>',
                unsafe_allow_html=True,
            )
            return

        for index, source in enumerate(source_list, start=1):
            filename = source.get("filename") or source.get("document_name") or "Unknown file"
            page = source.get("page_number")
            chunk = source.get("chunk_index")
            score = source.get("score")
            if score is None:
                score = source.get("similarity_score")
            try:
                score_label = f"{float(score):.2f}"
            except (TypeError, ValueError):
                score_label = str(score or "-")
            preview = (
                source.get("text_preview")
                or source.get("chunk_text")
                or source.get("content")
                or "No passage preview was returned."
            )
            label = f"{index}.  {filename}"
            with st.expander(label, expanded=True):
                st.markdown(
                    '<div class="evidence-card-detail-row">'
                    f'<span>Page {_safe(page)} &nbsp;·&nbsp; Chunk #{_safe(chunk)}</span>'
                    f'<span class="evidence-expanded-score">{_safe(score_label)}</span>'
                    '</div>'
                    f'<div class="evidence-expanded-preview">{_safe(preview)}</div>',
                    unsafe_allow_html=True,
                )


def upload_processing_timeline(steps, states, overall_status="Ready"):
    state_config = {
        "complete": ("✓", ""),
        "running": ("●", '<span class="upload-step-state">Running</span>'),
        "queued": ("·", '<span class="upload-step-state">Queued</span>'),
        "failed": ("!", '<span class="upload-step-state">Failed</span>'),
    }
    items = []
    for index, (name, detail) in enumerate(steps):
        state = states[index] if index < len(states) else "queued"
        if state not in state_config:
            state = "queued"
        icon, badge = state_config[state]
        items.append(
            f'<div class="upload-step upload-step-{state}">'
            f'<div class="upload-step-icon">{icon}</div>'
            '<div class="upload-step-copy">'
            f'<div class="upload-step-name">{_safe(name)}{badge}</div>'
            f'<div class="upload-step-detail">{_safe(detail)}</div>'
            '</div></div>'
        )

    st.markdown(
        '<section class="upload-timeline-panel">'
        '<div class="upload-timeline-head"><div>'
        '<div class="upload-timeline-title">Processing Timeline</div>'
        '<div class="upload-timeline-subtitle">Live status for the most recent upload</div>'
        f'</div><div class="upload-timeline-status">{_safe(overall_status)}</div></div>'
        f'{"".join(items)}</section>',
        unsafe_allow_html=True,
    )


def upload_success_panel(filename, file_size, total_chunks, status):
    st.markdown(
        '<section class="upload-success-panel">'
        '<div class="upload-success-icon">✓</div>'
        '<div><div class="upload-success-title">'
        f'{_safe(filename)} processed successfully</div>'
        '<div class="upload-success-subtitle">Available now in your knowledge base for hybrid retrieval.</div>'
        '<div class="upload-success-stats">'
        '<div class="upload-success-stat"><div class="upload-success-label">Filename</div>'
        f'<div class="upload-success-value">{_safe(filename)}</div></div>'
        '<div class="upload-success-stat"><div class="upload-success-label">File size</div>'
        f'<div class="upload-success-value">{_safe(file_size)}</div></div>'
        '<div class="upload-success-stat"><div class="upload-success-label">Total chunks</div>'
        f'<div class="upload-success-value">{_safe(total_chunks)}</div></div>'
        '<div class="upload-success-stat"><div class="upload-success-label">Status</div>'
        f'<div class="upload-success-value">{_safe(status)}</div></div>'
        '</div></div>'
        '<a class="upload-documents-link" href="Documents" target="_self">View documents&nbsp;&nbsp; →</a>'
        '</section>',
        unsafe_allow_html=True,
    )


def source_card(index: int, source: dict):
    filename = source.get("filename") or "Unknown file"
    score = source.get("score")
    score_text = f"{score:.3f}" if isinstance(score, (int, float)) else (score or "-")
    st.markdown(
        f'<div class="source-card"><div class="source-card-header"><span class="source-title">[{index}] {_safe(filename)}</span>'
        f'<span class="source-meta">score {_safe(score_text)}</span></div>'
        f'<div class="faint">Page {_safe(source.get("page_number"))} · Chunk {_safe(source.get("chunk_index"))}</div>'
        f'<div class="source-preview">{_safe(source.get("text_preview"), "No preview available")}</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, message: str, icon: str = "○"):
    st.markdown(
        f'<div class="empty-state"><div style="font-size:22px; margin-bottom:10px;">{_safe(icon)}</div>'
        f'<div class="empty-state-title">{_safe(title)}</div><div class="small-muted">{_safe(message)}</div></div>',
        unsafe_allow_html=True,
    )


def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)


def card_close():
    st.markdown('</div>', unsafe_allow_html=True)
