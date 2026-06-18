# ------------------------------------------------IMPORTS------------------------------------------------
import os

import asyncio
import streamlit as st
from backend import (
    workflow, get_model_title, retrieve_all_threads,
    save_title, get_title, title_exists, run_async,
    ingest_pdf, thread_document_metadata, transcribe_audio
)
import uuid
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.types import Command


# ------------------------------------------------Set Page Title------------------------------------------------

st.set_page_config(page_title="BodhanAI")

# ------------------------------------------------UTILITY Fxns------------------------------------------------

def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    st.session_state["ingested_docs"].setdefault(str(thread_id), {})
    add_thread(thread_id)
    st.session_state["messages"] = []

def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def load_conv(thread_id):
    state = run_async(workflow.aget_state(config={"configurable": {"thread_id": thread_id}}))
    if state and state.values:
        return state.values.get("messages", [])
    return []


def extract_text(content) -> str:
    """
    Gemini (langchain-google-genai) returns AIMessage.content as either:
      - a plain string, or
      - a list of content blocks: [{'type': 'text', 'text': '...', 'extras': {...}}, ...]

    Streaming chunks follow the same pattern.

    This helper always returns a clean plain-text string so we never
    accidentally render raw Python reprs (including the 'extras'/'signature'
    blobs) in the UI.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


def messages_to_display(raw_messages):
    """Convert LangChain messages to simple role/content dicts, skipping ToolMessages."""
    result = []
    for msg in raw_messages:
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": extract_text(msg.content)})
        elif isinstance(msg, AIMessage):
            text = extract_text(msg.content)
            if text:
                result.append({"role": "assistant", "content": text})
    return result

# ------------------------------------------------STARTUP------------------------------------------------

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()
if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()
if "ingested_docs" not in st.session_state:
    st.session_state["ingested_docs"] = {}
if "pending_interrupt" not in st.session_state:
    st.session_state["pending_interrupt"] = None
if "waiting_for_human" not in st.session_state:
    st.session_state["waiting_for_human"] = False
if "last_audio_id" not in st.session_state:
    st.session_state["last_audio_id"] = None

add_thread(st.session_state["thread_id"])

# ------------------------------------------------RECOMPUTE EVERY RERUN------------------------------------------------

thread_key = str(st.session_state["thread_id"])
thread_docs = st.session_state["ingested_docs"].setdefault(thread_key, {})

CONFIG = {
    "configurable": {"thread_id": thread_key},
    "metadata": {"thread_id": thread_key, "run_name": "chat_turn"},
}

# ------------------------------------------------Sidebar------------------------------------------------

st.sidebar.title("Workbench")

if st.sidebar.button("New Chat"):
    reset_chat()
    st.rerun()

st.sidebar.subheader("📄 PDF Upload")

if thread_docs:
    latest = list(thread_docs.values())[-1]
    st.sidebar.success(
        f"Using `{latest.get('filename')}` "
        f"({latest.get('chunks')} chunks, {latest.get('documents')} pages)"
    )
else:
    st.sidebar.info("No PDF indexed for this chat.")

uploaded_pdf = st.sidebar.file_uploader("Upload a PDF for this chat", type=["pdf"])
if uploaded_pdf:
    if uploaded_pdf.name in thread_docs:
        st.sidebar.info(f"`{uploaded_pdf.name}` already processed.")
    else:
        with st.sidebar.status("Indexing PDF…", expanded=True) as status_box:
            summary = ingest_pdf(
                uploaded_pdf.getvalue(),
                thread_id=thread_key,
                filename=uploaded_pdf.name,
            )
            thread_docs[uploaded_pdf.name] = summary
            status_box.update(label="✅ PDF indexed", state="complete", expanded=False)

st.sidebar.subheader("Recents")
for thread_id in reversed(st.session_state["chat_threads"]):
    title = get_title(thread_id)
    if st.sidebar.button(title, key=f"thread-{thread_id}"):
        st.session_state["thread_id"] = thread_id
        st.session_state["messages"] = messages_to_display(load_conv(thread_id))
        st.session_state["ingested_docs"].setdefault(str(thread_id), {})
        st.rerun()

# ------------------------------------------------Displaying Messages------------------------------------------------

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ------------------------------------------------HITL Confirmation UI------------------------------------------------

if st.session_state["waiting_for_human"]:
    interrupt_obj = st.session_state["pending_interrupt"]
    st.warning(interrupt_obj.value)

    def _resume_and_reload(decision: str):
        run_async(
            workflow.ainvoke(
                Command(resume=decision),
                config=CONFIG,
            )
        )
        st.session_state["pending_interrupt"] = None
        st.session_state["waiting_for_human"] = False
        st.session_state["messages"] = messages_to_display(
            load_conv(st.session_state["thread_id"])
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes"):
            _resume_and_reload("yes")
            st.rerun()
    with col2:
        if st.button("❌ No"):
            _resume_and_reload("no")
            st.rerun()

# ------------------------------------------------Audio Input------------------------------------------------

audio_value = st.audio_input("🎙️ Speak your message")

# ------------------------------------------------Voice Transcription (loop-safe)------------------------------------------------

voice_prompt = None
if audio_value is not None:
    audio_id = hash(audio_value.getvalue())
    if audio_id != st.session_state["last_audio_id"]:
        with st.spinner("Transcribing..."):
            voice_prompt = transcribe_audio(audio_value.getvalue(), file_extension="wav")
        st.session_state["last_audio_id"] = audio_id
        st.info(f"Transcribed: *{voice_prompt}*")

# ------------------------------------------------Chat Input + Streaming------------------------------------------------

prompt = st.chat_input(
    "Ask Anything.....",
    disabled=st.session_state["waiting_for_human"]
)

effective_prompt = voice_prompt or prompt

if effective_prompt and not st.session_state["waiting_for_human"]:
    with st.chat_message("user"):
        st.markdown(effective_prompt)
    st.session_state["messages"].append({"role": "user", "content": effective_prompt})

    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_only_stream():
            async def _astream():
                async for message_chunk, metadata in workflow.astream(
                    {"messages": [HumanMessage(content=effective_prompt)]},
                    config=CONFIG,
                    stream_mode="messages",
                ):
                    if isinstance(message_chunk, ToolMessage):
                        tool_name = getattr(message_chunk, "name", "tool")
                        yield ("tool", tool_name)
                    if isinstance(message_chunk, AIMessage):
                        text = extract_text(message_chunk.content)
                        if text:
                            yield ("text", text)

            async_gen = _astream()
            while True:
                try:
                    kind, value = run_async(async_gen.__anext__())
                    if kind == "tool":
                        if status_holder["box"] is None:
                            status_holder["box"] = st.status(f"🔧 Using `{value}` …", expanded=True)
                        else:
                            status_holder["box"].update(label=f"🔧 Using `{value}` …", state="running", expanded=True)
                    elif kind == "text":
                        yield value
                except StopAsyncIteration:
                    break

        ai_msg = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            status_holder["box"].update(label="✅ Tool finished", state="complete", expanded=True)

    # Check if graph paused at a HITL interrupt
    state = run_async(workflow.aget_state(CONFIG))
    if state.interrupts:
        st.session_state["pending_interrupt"] = state.interrupts[0]
        st.session_state["waiting_for_human"] = True

    if ai_msg:
        st.session_state["messages"].append({"role": "assistant", "content": ai_msg})

    doc_meta = thread_document_metadata(thread_key)
    if doc_meta:
        st.caption(f"Document: `{doc_meta.get('filename')}` — {doc_meta.get('chunks')} chunks, {doc_meta.get('documents')} pages")

    if not title_exists(thread_key):
        title = run_async(get_model_title(st.session_state["messages"]))
        save_title(thread_key, title)

    st.rerun()
