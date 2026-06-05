# ------------------------------------------------IMPORTS------------------------------------------------

import streamlit as st
from backend import workflow,get_model_title,retrieve_all_threads,save_title,get_title,title_exists
import uuid
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import List

# ------------------------------------------------Set Page Title------------------------------------------------
st.set_page_config(page_title="BodhanAI")

# ------------------------------------------------Custom Button Styling------------------------------------------------
st.markdown("""
<style>
    /* New Chat Button */
    div[data-testid="stVerticalBlock"] > [data-testid="stButton"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    div[data-testid="stVerticalBlock"] > [data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Thread Buttons in Sidebar */
    div[data-testid="stSidebar"] [data-testid="stButton"] button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        width: 100%;
        padding: 10px 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
        margin: 4px 0;
    }
    
    div[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(245, 87, 108, 0.5);
        background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
    }
</style>
""", unsafe_allow_html=True)

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

    with st.chat_message("assistant"):
        ai_msg = st.write_stream(
            message_chunk.content for message_chunk,metadata in workflow.stream(
                {'messages':[HumanMessage(content=prompt)]},
                config= CONFIG,
                stream_mode= 'messages'
            )
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