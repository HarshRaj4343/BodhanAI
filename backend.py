from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
import streamlit as st
import os

load_dotenv()

# Get Groq API key from Streamlit Secrets (cloud) or environment variable (local)
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("API key not found. Please add GROQ_API_KEY to Streamlit Secrets.")
    st.stop()

# Use Groq - much faster and better!
llm = ChatGroq(
    model="mixtral-8x7b-32768",
    api_key=groq_api_key,
    temperature=0.7,
    max_tokens=256
)

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def chat_node(state: ChatState) -> ChatState:
    messages = state["messages"]
    
    system_msg = SystemMessage(
        content="You are a helpful and concise chatbot. Provide direct, clear answers without overthinking or verbose explanations."
    )
    
    conversation = [system_msg] + messages
    
    # Get response from Groq LLM
    response = llm.invoke(conversation)
    
    return {'messages': [response]}


checkpointer = InMemorySaver()
graph = StateGraph(ChatState)

graph.add_node("Chat Node", chat_node)
graph.add_edge(START, "Chat Node")
graph.add_edge("Chat Node", END)

workflow = graph.compile(checkpointer=checkpointer)
