import streamlit as st
from backend import workflow,get_model_title,retrieve_all_threads
import uuid
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import List

# PAGE TITLE 
st.set_page_config(page_title="BodhanAI")


# UTILITY Functions
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
    return workflow.get_state(config={'configurable':{'thread_id': st.session_state['thread_id']}}).values['messages']

# STARTUP Functions

if "messages" not in st.session_state:
    st.session_state['messages'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
if "chat_threads" not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()
add_thread(st.session_state['thread_id'])

# CONFIG
CONFIG = {'configurable':{'thread_id': st.session_state['thread_id']}}


# Lander Page - Title, Welcome Message + Message History printer

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');

    /* Top-left company name */
    .company-name {
        position: fixed;
        top: 49px;
        left: 40px;
        font-size: 32px;
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
    }

    /* Welcome banner */
    .banner-name {
        position: fixed;
        top: 350px;
        left: 650px;
        font-size: 32px;
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
    }
    </style>
        """,
     unsafe_allow_html=True
     )

st.markdown('<div class="company-name">BodhanAI</div>', unsafe_allow_html=True)

# Sidebar Settings

st.sidebar.title("Workbench")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("Recents")

for thread_id in reversed(st.session_state['chat_threads']):
    if st.sidebar.button(get_model_title(st.session_state.messages), key=f"thread-{thread_id}"):
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


for message in (st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.messages:
    st.markdown('<div class="banner-name">Ready to dive in?</div>', unsafe_allow_html=True)

prompt = st.chat_input("Ask Anything.....")


# Recent Message Display

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
    
    st.session_state.messages.append({"role": "assistant", "content": ai_msg})
    
    st.rerun()
