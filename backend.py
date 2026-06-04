from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage # Added SystemMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
import operator
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

llm = HuggingFaceEndpoint(
    repo_id="openai/gpt-oss-20b", 
    task="text-generation"
)

model = ChatHuggingFace(llm=llm)

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def chat_node(state: ChatState) -> ChatState:
    messages = state["messages"]
    
    system_msg = SystemMessage(
        content="You are a chatbot. Provide precise answers to given prompts asked by users."
    )
    
    conversation = [system_msg] + messages
    
    response = model.invoke(conversation)
    
    return {'messages': [response]}


checkpointer = InMemorySaver()
graph = StateGraph(ChatState)

graph.add_node("Chat Node", chat_node)
graph.add_edge(START, "Chat Node")
graph.add_edge("Chat Node", END)

workflow = graph.compile(checkpointer=checkpointer)