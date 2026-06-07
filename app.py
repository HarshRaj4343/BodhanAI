# ------------------------------------------------IMPORTS------------------------------------------------

import streamlit as st
from backend import workflow,get_model_title,retrieve_all_threads,save_title,get_title,title_exists
import uuid
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from typing import List

# ------------------------------------------------Set Page Title------------------------------------------------
st.set_page_config(page_title="BodhanAI")

# ------------------------------------------------UTILITY Fxns------------------------------------------------
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['messages'] = []
def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
def load_conv(thread_id):
    state = workflow.get_state(config={'configurable':{'thread_id': st.session_state['thread_id']}})
    if state and state.values:
        return state.values.get('messages', [])
    return []

# ------------------------------------------------STARTUP Fxns------------------------------------------------

if "messages" not in st.session_state:
    st.session_state['messages'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
if "chat_threads" not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()
add_thread(st.session_state['thread_id'])

# ------------------------------------------------CONFIG------------------------------------------------

# CONFIG = {
#     "configurable": {"thread_id": st.session_state["thread_id"]}}

# this config is just adding threading during langsmith integration
CONFIG = {
    "configurable": {"thread_id": st.session_state["thread_id"]},
    "metadata": {
    "thread_id": st.session_state["thread_id"],
    "run_name": "chat_turn"
}
}


# ------------------------------------------------Sidebar Settings------------------------------------------------

st.sidebar.title("Workbench")
if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("Recents")

for thread_id in reversed(st.session_state['chat_threads']):
    title = get_title(thread_id)
    if st.sidebar.button(title, key=f"thread-{thread_id}"):
        st.session_state['thread_id'] = thread_id
        response = load_conv(thread_id=thread_id)

        temp_messages = []
        for msg in response:
            if isinstance(msg,HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({"role":role,"content":msg.content})
        st.session_state['messages']= temp_messages

# ------------------------------------------------Displaying the Messages------------------------------------------------

for message in (st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ------------------------------------------------Taking User's Prompt------------------------------------------------

prompt = st.chat_input("Ask Anything.....")


# ------------------------------------------------Recent Message Display + Streaming------------------------------------------------

if prompt:

    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Assistant streaming block
    with st.chat_message("assistant"):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in workflow.stream(
                {"messages": [HumanMessage(content=prompt)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content
        ai_msg = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=True
            )

# applied title storage in sql

    st.session_state.messages.append(
    {
        "role": "assistant",
        "content": ai_msg
    }
)
    thread_id = st.session_state["thread_id"]

    if not title_exists(thread_id):

        title = get_model_title(
            st.session_state.messages
        )

        save_title(
            thread_id,
            title
        )

    st.rerun()