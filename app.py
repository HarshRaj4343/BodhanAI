import streamlit as st
from backend import workflow
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
# Configure page
st.set_page_config(page_title="Bodha")

thread_id = '1'
CONFIG = {'configurable':{'thread_id': thread_id}}

# 1. Initialize chat history at the very top
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Render Custom CSS + HTML Layout
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

st.markdown('<div class="company-name">Bodha</div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.messages:
    st.markdown('<div class="banner-name">Ready to dive in, Harsh?</div>', unsafe_allow_html=True)

prompt = st.chat_input("Ask Anything.....")

if prompt:

    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        ai_msg = st.write_stream(
            message_chunk.content for message_chunk,metadata in workflow.stream(
                {'messages':[HumanMessage(content=prompt)]},
                config= {'configurable':{"thread_id": thread_id}},
                stream_mode= 'messages'
            )
        )
    
    st.session_state.messages.append({"role": "assistant", "content": ai_msg})
    
    st.rerun()
