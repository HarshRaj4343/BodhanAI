from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_huggingface import HuggingFaceEndpoint
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
import streamlit as st
import os
import re

load_dotenv()

api_token = st.secrets.get("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")

if not api_token:
    st.error("API key not found. Please add HUGGINGFACEHUB_API_TOKEN to Streamlit Secrets.")
    st.stop()

llm = HuggingFaceEndpoint(
    repo_id="deepseek-ai/DeepSeek-R1",
    huggingfacehub_api_token=api_token,
    task="text-generation",
    model_kwargs={
        "temperature": 0.7,
        "max_new_tokens": 512,
    }
)

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def extract_final_answer(response_text: str) -> str:
    """Extract only the final answer, removing thinking/reasoning blocks"""
    
    
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
    
    response_text = re.sub(r'\n*#{1,6}\s*.*thinking.*?\n', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'\n*\*\*.*?thinking.*?\*\*\n', '', response_text, flags=re.IGNORECASE)
    
    response_text = re.sub(r'^.*?(let me|i think|hmm|so|therefore|conclusion):?\s*', '', response_text, flags=re.IGNORECASE | re.MULTILINE)
    
    
    lines = response_text.strip().split('\n')
    final_answer = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('---') and not line.startswith('###'):
            final_answer.append(line)
    
    result = '\n'.join(final_answer).strip()
    
    if len(result) > 500:
        sentences = result.split('.')
        result = sentences[0] + '.'
    
    return result if result else "I couldn't generate a proper response."

def chat_node(state: ChatState) -> ChatState:
    messages = state["messages"]
    
    user_message = messages[-1].content if messages else ""
    
    prompt = f"""Answer this directly and concisely: {user_message}"""
    
    response_text = llm.invoke(prompt)
    
   
    clean_response = extract_final_answer(response_text)
    
    
    ai_message = AIMessage(content=clean_response)
    
    return {'messages': [ai_message]}


checkpointer = InMemorySaver()
graph = StateGraph(ChatState)

graph.add_node("Chat Node", chat_node)
graph.add_edge(START, "Chat Node")
graph.add_edge("Chat Node", END)

workflow = graph.compile(checkpointer=checkpointer)
