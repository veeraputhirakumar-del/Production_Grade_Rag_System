import html
import os

import streamlit as st

from api_client import ask_question
from styles import (
    apply_custom_css,
    chat_evidence_panel,
    chat_retrieval_panel,
)


st.set_page_config(
    page_title="Chat · Production Grade RAG System",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css()


CHAT_MODES = {
    "Normal": "Answer normally using the uploaded document context.",
    "Simple": "Explain in very simple beginner-friendly words.",
    "Detailed": "Give a detailed explanation with clear structure and examples.",
    "Bullet Points": "Answer using concise, well-organized bullet points.",
    "Interview Prep": "Answer like an interview response with key points and examples.",
    "Summary": "Give a short summary containing only the most important information.",
}

MODEL_LABEL = os.getenv("MODEL_LABEL", "llama3.2:8b")
VECTOR_DB_LABEL = os.getenv("VECTOR_DB_LABEL", "ChromaDB")
SEARCH_TYPE_LABEL = os.getenv("SEARCH_TYPE_LABEL", "Hybrid (BM25 + Vec)")
MAX_SOURCES = int(os.getenv("MAX_SOURCES", "6"))
RETRIEVAL_CANDIDATES = int(os.getenv("RETRIEVAL_CANDIDATES", "12"))


def init_state():
    defaults = {
        "chat_messages": [],
        "message_meta": {},
        "chat_mode": "Normal",
        "pending_question": None,
        "chat_feedback": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_chat():
    st.session_state.chat_messages = []
    st.session_state.message_meta = {}
    st.session_state.pending_question = None
    st.session_state.chat_feedback = {}
    st.session_state.chat_mode = "Normal"
    st.session_state.pop("composer_mode", None)


def build_mode_question(question: str, mode: str) -> str:
    instruction = CHAT_MODES.get(mode, CHAT_MODES["Normal"])
    return f"{question}\n\nAnswer mode instruction: {instruction}"


def previous_user_question(assistant_index: int):
    for index in range(assistant_index - 1, -1, -1):
        message = st.session_state.chat_messages[index]
        if message.get("role") == "user":
            return message.get("content")
    return None


def regenerate_answer(assistant_index: int):
    question = previous_user_question(assistant_index)
    if not question:
        return

    st.session_state.chat_messages = st.session_state.chat_messages[:assistant_index]
    st.session_state.message_meta = {
        index: meta
        for index, meta in st.session_state.message_meta.items()
        if index < assistant_index
    }
    st.session_state.pending_question = question
    st.rerun()


def render_answer_actions(message_index: int, answer: str):
    current_feedback = st.session_state.chat_feedback.get(message_index)
    action_cols = st.columns([1.35, 1.65, 1.15, 1.1, 3.75], gap="small")

    with action_cols[0]:
        st.download_button(
            "Copy",
            data=answer,
            file_name="rag_answer.txt",
            mime="text/plain",
            icon=":material/content_copy:",
            key=f"copy_{message_index}",
            help="Save a plain-text copy of this answer",
        )
    with action_cols[1]:
        if st.button(
            "Regenerate",
            icon=":material/refresh:",
            key=f"regenerate_{message_index}",
        ):
            regenerate_answer(message_index)
    with action_cols[2]:
        if st.button(
            "Good" if current_feedback != "good" else "✓ Good",
            icon=":material/thumb_up:",
            key=f"good_{message_index}",
        ):
            st.session_state.chat_feedback[message_index] = "good"
            st.rerun()
    with action_cols[3]:
        if st.button(
            "Bad" if current_feedback != "bad" else "✓ Bad",
            icon=":material/thumb_down:",
            key=f"bad_{message_index}",
        ):
            st.session_state.chat_feedback[message_index] = "bad"
            st.rerun()


def render_conversation():
    if not st.session_state.chat_messages:
        st.markdown(
            """
            <div class="chat-welcome">
                <div class="chat-welcome-icon">✦</div>
                <div class="chat-welcome-title">Ready when you are</div>
                <div class="chat-welcome-copy">Ask anything about your uploaded documents.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for index, message in enumerate(st.session_state.chat_messages):
        role = message.get("role", "assistant")
        if role == "user":
            question = html.escape(str(message.get("content", ""))).replace("\n", "<br>")
            st.markdown(
                f'<div class="chat-user-row"><div class="chat-user-bubble">{question}</div></div>',
                unsafe_allow_html=True,
            )
            continue

        with st.chat_message("assistant", avatar=":material/auto_awesome:"):
            meta = st.session_state.message_meta.get(index, {})
            latency = meta.get("latency_ms")
            try:
                latency_label = f"{float(latency) / 1000:.2f}s"
            except (TypeError, ValueError):
                latency_label = "-"
            st.markdown(
                f'<div class="assistant-byline">Production Grade RAG System · {MODEL_LABEL} &nbsp;·&nbsp; ◔ {latency_label}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(message.get("content", ""))
            render_answer_actions(index, message.get("content", ""))


def process_question(question: str, mode: str):
    result = ask_question(build_mode_question(question, mode))

    if result.get("success"):
        answer = result.get("answer") or "No answer was returned."
        assistant_index = len(st.session_state.chat_messages)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.session_state.message_meta[assistant_index] = {
            "sources": result.get("sources", []),
            "latency_ms": result.get("latency_ms"),
            "question_id": result.get("question_id"),
        }
    else:
        error = result.get("error", "An unknown backend error occurred.")
        assistant_index = len(st.session_state.chat_messages)
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": f"I could not generate an answer. {error}"}
        )
        st.session_state.message_meta[assistant_index] = {
            "sources": [],
            "latency_ms": None,
            "question_id": None,
        }
    st.rerun()


init_state()

with st.container(key="chat_simple_header"):
    title_col, action_col = st.columns([0.82, 0.18], vertical_alignment="center")
    with title_col:
        st.markdown(
            """
            <div class="upload-page-header chat-title-block">
                <h1>Ask Your Knowledge Base</h1>
                <p>Search uploaded documents using hybrid retrieval and your local LLM.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with action_col:
        if st.button("＋  New chat", width="stretch", key="new_chat"):
            clear_chat()
            st.rerun()

    st.markdown(
        """
        <div class="upload-capability-row chat-header-capabilities">
            <span>Hybrid Retrieval</span>
            <span>Source Citations</span>
            <span>Local LLM</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="chat-single-divider"></div>', unsafe_allow_html=True)

with st.container(key="chat_shell"):
    with st.container(key="chat_conversation"):
        render_conversation()

        pending_question = st.session_state.pending_question
        if pending_question:
            st.markdown(
                """
                <div class="assistant-generating-row">
                    <div class="assistant-generating-icon">✦</div>
                    <div>
                        <div class="assistant-generating-label">RAG System is preparing your answer</div>
                        <div class="assistant-generating-stages">
                            <span>Retrieving</span><span>Reranking</span><span>Generating</span>
                        </div>
                        <div class="assistant-generating-dots"><span></span><span></span><span></span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.form("chat_composer", clear_on_submit=True, border=False):
        attach_col, input_col, mode_col, send_col = st.columns(
            [0.05, 0.62, 0.19, 0.14],
            vertical_alignment="center",
            gap="small",
        )
        with attach_col:
            st.markdown(
                '<a class="composer-attach-link" href="Upload" target="_self" '
                'title="Upload documents">&#128206;</a>',
                unsafe_allow_html=True,
            )
        with input_col:
            typed_question = st.text_input(
                "Question",
                placeholder="Ask anything from your documents...",
                label_visibility="collapsed",
                disabled=bool(pending_question),
            )
        with mode_col:
            mode_options = list(CHAT_MODES.keys())
            selected_mode = st.selectbox(
                "Answer mode",
                mode_options,
                index=mode_options.index(st.session_state.chat_mode),
                label_visibility="collapsed",
                disabled=bool(pending_question),
                key="composer_mode",
            )
        with send_col:
            submitted = st.form_submit_button(
                "➤  Send",
                width="stretch",
                disabled=bool(pending_question),
            )

    if selected_mode:
        st.session_state.chat_mode = selected_mode

    composer_meta, composer_shortcut = st.columns([0.7, 0.3])
    with composer_meta:
        st.markdown(
            f'<div class="chat-input-meta">Hybrid retrieval · {MAX_SOURCES} sources max · {MODEL_LABEL}</div>',
            unsafe_allow_html=True,
        )
    with composer_shortcut:
        st.markdown(
            '<div class="chat-input-shortcut">Ctrl + Enter to send</div>',
            unsafe_allow_html=True,
        )

    if pending_question:
        st.session_state.pending_question = None
        process_question(pending_question, st.session_state.chat_mode)
    elif submitted and typed_question.strip():
        question = typed_question.strip()
        st.session_state.chat_messages.append({"role": "user", "content": question})
        st.session_state.pending_question = question
        st.rerun()

assistant_indices = [
    index
    for index, message in enumerate(st.session_state.chat_messages)
    if message.get("role") == "assistant"
]
if assistant_indices:
    latest_meta = st.session_state.message_meta.get(assistant_indices[-1], {})
    latest_sources = latest_meta.get("sources", [])
    chat_evidence_panel(latest_sources)
    chat_retrieval_panel(
        sources_found=len(latest_sources),
        max_sources=RETRIEVAL_CANDIDATES,
        latency_ms=latest_meta.get("latency_ms"),
        search_type=SEARCH_TYPE_LABEL,
        vector_db=VECTOR_DB_LABEL,
        model=MODEL_LABEL,
    )
