# ------------------------------------------------IMPORTS------------------------------------------------

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import streamlit as st
import os
import sqlite3

# ------------------------------------------------CONNECTING .env------------------------------------------------

load_dotenv()

# ------------------------------------------------SETTING UP LLM------------------------------------------------

# Get Groq API key from Streamlit Secrets (cloud) or environment variable (local)
groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not groq_api_key:
    st.error("API key not found. Please add GROQ_API_KEY to Streamlit Secrets.")
    st.stop()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=groq_api_key,
    temperature=0.7
)

# ------------------------------------------------Conversation Title Maker------------------------------------------------

def get_model_title(hist: List):
    prompt = f"""You are an expert conversation summarizer.

        Your task is to generate a concise title for a chatbot conversation.

        Rules:
        - Return ONLY the title.
        - Maximum 6 words.
        - Prefer 2 to 5 words when possible.
        - Capture the main topic, intent, or problem discussed.
        - Do not use quotation marks, punctuation, emojis, or prefixes like "Title:".
        - Use title case.
        - Be specific rather than generic.
        - If the conversation is about debugging, mention the technology and issue.
        - If multiple topics exist, focus on the primary one.
        - Do not explain your reasoning.

        Conversation:
        {hist}
        Title:
        """
    response = llm.invoke(prompt)
    return response.content

# ------------------------------------------------Setting up the Graph------------------------------------------------


class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def chat_node(state: ChatState) -> ChatState:
    messages = state["messages"]
    
    system_msg = SystemMessage(
        content="You are a helpful and concise chatbot. Your name is BodhanAI. Provide direct, clear answers without overthinking or verbose explanations."
    )
    
    conversation = [system_msg] + messages
    
    response = llm.invoke(conversation)
    
    return {'messages': [response]}

# ------------------------------------------------Connecting to SQLite------------------------------------------------

conn = sqlite3.connect(database='bodhanai',check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

cursor = conn.cursor()

cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_titles (
            thread_id TEXT PRIMARY KEY,
            title TEXT
        )
""")

conn.commit()

# ------------------------------------------------Making the Graph------------------------------------------------

graph = StateGraph(ChatState)
graph.add_node("Chat Node", chat_node)
graph.add_edge(START, "Chat Node")
graph.add_edge("Chat Node", END)

workflow = graph.compile(checkpointer=checkpointer)

# ------------------------------------------------fetch all unique conversation thread IDs------------------------------------------------

def retrieve_all_threads():
    all_threads = set()
    # Assuming 'checkpointer' is your SQLite checkpointer instance
    for checkpoint in checkpointer.list(None):
        thread_id = checkpoint.config["configurable"]["thread_id"]
        all_threads.add(thread_id)
    return list(all_threads)

# ------------------------------------------------Chat Title Utility Fxns------------------------------------------------

def save_title(thread_id, title):
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO chat_titles
    (thread_id, title)
    VALUES (?, ?)
    """, (str(thread_id), title))

    conn.commit()


def get_title(thread_id):
    cursor = conn.cursor()

    cursor.execute("""
    SELECT title
    FROM chat_titles
    WHERE thread_id = ?
    """, (str(thread_id),))

    result = cursor.fetchone()

    if result:
        return result[0]

    return "New Chat"


def title_exists(thread_id):
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 1
    FROM chat_titles
    WHERE thread_id = ?
    """, (str(thread_id),))

    return cursor.fetchone() is not None