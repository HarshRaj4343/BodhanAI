# ------------------------------------------------IMPORTS------------------------------------------------

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import streamlit as st
import os
import aiosqlite
import aiohttp
import asyncio
import threading
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_tavily import TavilySearch
from langchain_core.tools import tool,BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
# ------------------------------------------------CONNECTING .env------------------------------------------------

load_dotenv()

# ------------------------------------------------ASYNC LOOP SETUP------------------------------------------------

_ASYNC_LOOP = asyncio.new_event_loop()
_ASYNC_THREAD = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
_ASYNC_THREAD.start()

def _submit_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)

def run_async(coro):
    return _submit_async(coro).result()

def submit_async_task(coro):
    """Schedule a coroutine on the backend event loop."""
    return _submit_async(coro)
# ------------------------------------------------SETTING UP LLM------------------------------------------------

groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not groq_api_key:
    st.error("API key not found. Please add GROQ_API_KEY to Streamlit Secrets.")
    st.stop()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
)

tavily_key = os.getenv("TAVILY_API_KEY") or st.secrets["TAVILY_API_KEY"]

# ------------------------------------------------Setting up Tools------------------------------------------------

search_tool = TavilySearch(
    max_results=3,
    search_depth="basic",
    include_answer=True,
)


@tool
async def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol.
    """
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE"
        f"&symbol={symbol}"
        f"&apikey=QPBT1S9TKAAET4CS"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()



# ------------------------------------------------Setting up the MCP------------------------------------------------

client = MultiServerMCPClient(
    {
        "date-time-tools": {
            "transport": "streamable_http",
            "url": "https://date-time-tools.iabhishek.workers.dev/mcp"
        }
    }
)
# ------------------------------------------------Loading the MCP tools------------------------------------------------
def load_mcp_tools() -> list[BaseTool]:
    try:
        return run_async(client.get_tools())
    except Exception as e:
        print(f"MCP loading failed: {e}")
        return []
mcp_tools = load_mcp_tools()

# ------------------------------------------------Binding the tools------------------------------------------------
tools = [get_stock_price, search_tool,*mcp_tools]

llm_with_tools = llm.bind_tools(tools) if tools else llm

# ------------------------------------------------Conversation Title Maker------------------------------------------------

async def get_model_title(hist: List):
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
        - the main thing is that this title is to be seen by user , so make it seem like it is for a user : like first person view

        Conversation:
        {hist}
        Title:
        """
    response = await llm.ainvoke(prompt)
    return response.content

# ------------------------------------------------Setting up the Graph------------------------------------------------

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

async def chat_node(state: ChatState) -> ChatState:
    messages = state["messages"]
    
    system_msg = SystemMessage(
    content="""You are a helpful and concise chatbot. Your name is BodhanAI. Provide direct, clear answers without overthinking or verbose explanations. Never use LaTeX formatting (like \\[ or \\boxed) for math equations. Always use plain text and standard symbols (like * for multiplication).
            The user's GitHub username is: HarshRaj4343
            Always use this username when fetching GitHub data unless the user specifies otherwise."""
)
    
    conversation = [system_msg] + messages
    response = await llm_with_tools.ainvoke(conversation)
    return {'messages': [response]}

tool_node = ToolNode(tools) if tools else None

# ------------------------------------------------Connecting to SQLite------------------------------------------------

async def _init_checkpointer():
    conn = await aiosqlite.connect("bodhanai")
    saver = AsyncSqliteSaver(conn)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_titles (
            thread_id TEXT PRIMARY KEY,
            title TEXT
        )
    """)
    await conn.commit()
    return conn, saver

conn, checkpointer = run_async(_init_checkpointer())

# ------------------------------------------------Making the Graph------------------------------------------------

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")

if tool_node:
    graph.add_node("tools", tool_node)
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")
else:
    graph.add_edge("chat_node", END)

workflow = graph.compile(checkpointer=checkpointer)

# ------------------------------------------------fetch all unique conversation thread IDs------------------------------------------------

async def _alist_threads():
    all_threads = set()
    async for checkpoint in checkpointer.alist(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)

def retrieve_all_threads():
    return run_async(_alist_threads())

# ------------------------------------------------Chat Title Utility Fxns------------------------------------------------

async def _save_title(thread_id, title):
    await conn.execute("""
        INSERT OR REPLACE INTO chat_titles (thread_id, title)
        VALUES (?, ?)
    """, (str(thread_id), title))
    await conn.commit()

def save_title(thread_id, title):
    run_async(_save_title(thread_id, title))


async def _get_title(thread_id):
    async with conn.execute("""
        SELECT title FROM chat_titles WHERE thread_id = ?
    """, (str(thread_id),)) as cursor:
        result = await cursor.fetchone()
    return result[0] if result else "New Chat"

def get_title(thread_id):
    return run_async(_get_title(thread_id))


async def _title_exists(thread_id):
    async with conn.execute("""
        SELECT 1 FROM chat_titles WHERE thread_id = ?
    """, (str(thread_id),)) as cursor:
        return await cursor.fetchone() is not None

def title_exists(thread_id):
    return run_async(_title_exists(thread_id))