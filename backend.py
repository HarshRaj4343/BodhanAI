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
groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not groq_api_key:
    st.error("API key not found. Please add GROQ_API_KEY to Streamlit Secrets.")
    st.stop()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=groq_api_key,
    temperature=0.7
)

def get_model_title(hist: List):
    prompt = f"""You are an expert conversation summarizer.

        Your task is to generate a concise title for a chatbot conversation.

        Rules:
        - Return ONLY the title.
        - Maximum 6 words.
        - Prefer 2–5 words when possible.
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
    return response

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def chat_node(state: ChatState) -> ChatState:
    messages = state["messages"]
    
    system_msg = SystemMessage(
        content="You are a helpful and concise chatbot.Your name is BodhAI. Provide direct, clear answers without overthinking or verbose explanations."
    )
    
    conversation = [system_msg] + messages
    
    response = llm.invoke(conversation)
    
    return {'messages': [response]}


checkpointer = InMemorySaver()
graph = StateGraph(ChatState)

graph.add_node("Chat Node", chat_node)
graph.add_edge(START, "Chat Node")
graph.add_edge("Chat Node", END)

workflow = graph.compile(checkpointer=checkpointer)

