<h1 align="center">
  <br>
  🧠 BodhanAI
  <br>
</h1>

<p align="center">
  <b>A powerful, tool-augmented AI chatbot built with Streamlit + LangGraph + Groq</b>
  <br/>
  <i>Real-time web search · Live stock prices · Date/time tools via MCP · Persistent memory</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangGraph-Workflow-green?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Groq-LLM-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/SQLite-Persistence-lightgrey?style=for-the-badge&logo=sqlite"/>
</p>

---

## ✨ What is BodhanAI?

BodhanAI is a fully-featured AI chatbot that goes far beyond basic Q&A. It runs in your browser, streams responses in real time, remembers your conversations across sessions, and can autonomously call external tools — searching the web, fetching live stock prices, and querying date/time services — all through a clean Streamlit interface.

---

## 🚀 Features at a Glance

| Category | Capability |
|---|---|
| 💬 **Chat** | Streaming responses, multi-turn memory, chat bubbles |
| 🔍 **Web Search** | Live Tavily-powered search with answer synthesis |
| 📈 **Stock Prices** | Real-time quotes via Alpha Vantage API |
| 🕐 **Date & Time** | Remote MCP tool server for date/time queries |
| 🐙 **GitHub Aware** | Knows your GitHub username, can answer repo questions |
| 🧵 **Multi-thread** | Multiple parallel conversations, each with its own memory |
| 📝 **Auto Titles** | LLM-generated conversation titles in the sidebar |
| 💾 **Persistence** | SQLite-backed checkpoints survive app restarts |
| ⚡ **Async Core** | Fully async backend with a dedicated event loop thread |
| 🛠️ **Tool UI** | Live status box shows which tool is running while streaming |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   app.py (Streamlit UI)          │
│  Sidebar · Chat bubbles · Streaming · Rerun      │
└────────────────────┬────────────────────────────┘
                     │ calls
┌────────────────────▼────────────────────────────┐
│               backend.py (LangGraph)             │
│                                                  │
│   START ──► chat_node ──► tools_condition        │
│                  ▲              │                │
│                  │         ┌────▼────┐           │
│                  └─────────┤ToolNode │           │
│                            └─────────┘           │
│   Tools: TavilySearch · get_stock_price · MCP    │
└────────────────────┬────────────────────────────┘
                     │ checkpoints
┌────────────────────▼────────────────────────────┐
│            SQLite  (AsyncSqliteSaver)            │
│    messages  ·  thread IDs  ·  chat_titles       │
└─────────────────────────────────────────────────┘
```

The graph is simple by design:

- Every user message enters `chat_node`.
- The LLM decides whether to call a tool or respond directly.
- If a tool is needed, `ToolNode` executes it and loops back to `chat_node`.
- The final assistant message streams to the UI.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Groq — `openai/gpt-oss-120b` |
| Orchestration | LangGraph (async StateGraph) |
| Tool: Web Search | LangChain Tavily (`TavilySearch`) |
| Tool: Stock Prices | Alpha Vantage API via `aiohttp` |
| Tool: Date & Time | MCP server via `langchain-mcp-adapters` |
| Persistence | SQLite via `aiosqlite` + `AsyncSqliteSaver` |
| Env Config | `python-dotenv` + Streamlit Secrets |
| Dev Env | Dev Containers (Codespaces / VS Code) |

---

## 📁 Project Structure

```
bodhanai/
├── app.py                     # Streamlit UI — chat, sidebar, streaming
├── backend.py                 # LangGraph graph, tools, async loop, SQLite
├── requirements.txt           # Python dependencies
├── README.md                  # You are here
├── .env.example               # Template for local secrets
├── .env                       # Your actual secrets (git-ignored)
├── .gitignore                 # Ignores venv, cache, .env, SQLite files
├── .devcontainer/
│   └── devcontainer.json      # Codespaces / VS Code dev container config
├── bodhanai                   # SQLite database (git-ignored)
├── bodhanai-shm               # SQLite shared memory (git-ignored)
└── bodhanai-wal               # SQLite write-ahead log (git-ignored)
```

---

## ⚙️ Installation

### 1 — Clone the repo

```bash
git clone https://github.com/HarshRaj4343/bodhanai.git
cd bodhanai
```

### 2 — Create a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Configuration

BodhanAI needs two API keys. Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

> **Streamlit Cloud?** Add these as secrets under **App Settings → Secrets** in TOML format:
> ```toml
> GROQ_API_KEY = "your_groq_api_key_here"
> TAVILY_API_KEY = "your_tavily_api_key_here"
> ```

If either key is missing, the app shows a clear error and stops safely.

---

## ▶️ Running the App

```bash
streamlit run app.py
```

Opens at: **http://localhost:8501**

---

## 🧩 Tools & Capabilities

### 🔍 Web Search — Tavily
BodhanAI can search the live web to answer questions about current events, recent news, or anything beyond its training data. Powered by `TavilySearch` with answer synthesis enabled.

### 📈 Stock Price Lookup
Ask about any stock ticker and BodhanAI fetches the latest price from the Alpha Vantage API using an async HTTP call — no scraping, no delays.

```
"What is the current price of AAPL?"
"How is TSLA doing today?"
```

### 🕐 Date & Time via MCP
BodhanAI connects to a remote **Model Context Protocol (MCP)** server to answer precise date and time questions. MCP tools are loaded dynamically at startup and bound directly into the LangGraph tool loop.

```
"What day of the week is July 4th 2026?"
"How many days until Christmas?"
```

### 🐙 GitHub Awareness
The system prompt is pre-loaded with your GitHub username (`HarshRaj4343`). BodhanAI can answer questions about your repositories without you needing to specify the username every time.

### 🔧 Live Tool Status
While a tool is running, a live status box appears in the chat UI:
```
🔧 Using `tavily_search_results_json` …
✅ Tool finished
```

---

## 💬 Using BodhanAI

1. Open the app in your browser.
2. Type any message in the **"Ask Anything....."** input.
3. Watch the response stream word by word.
4. Click **New Chat** in the sidebar to start a fresh conversation.
5. Browse and reopen previous conversations from **Recents** in the sidebar — each one is titled automatically by the LLM.

---

## 💾 Persistence & Memory

Every conversation is stored as a checkpointed LangGraph state in a local SQLite database:

```python
conn = await aiosqlite.connect("bodhanai")
saver = AsyncSqliteSaver(conn)
```

Conversation titles are stored in a separate `chat_titles` table:

```sql
CREATE TABLE IF NOT EXISTS chat_titles (
    thread_id TEXT PRIMARY KEY,
    title TEXT
)
```

Thread behaviour:
- Each new chat gets a `uuid4` thread ID.
- On restart, all previous thread IDs are recovered and shown in the sidebar.
- Selecting a recent chat reloads its full message history from the checkpoint.

---

## 🔄 Async Architecture

BodhanAI runs a **dedicated background event loop** on a daemon thread so that async LangGraph and tool calls can work seamlessly inside Streamlit's synchronous execution model:

```python
_ASYNC_LOOP = asyncio.new_event_loop()
_ASYNC_THREAD = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
_ASYNC_THREAD.start()
```

All async functions are submitted via `run_async()` or `submit_async_task()` helpers that bridge sync Streamlit code to the async backend.

---

## 🚢 Deployment

### Streamlit Cloud

1. Push your repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app.
3. Set the entry point to `app.py`.
4. Add `GROQ_API_KEY` and `TAVILY_API_KEY` in **Secrets**.
5. Deploy. ✅

### Codespaces / Dev Containers

The repo includes `.devcontainer/devcontainer.json` which:
- Uses a **Python 3.11 Bookworm** image.
- Auto-installs all `requirements.txt` dependencies.
- Auto-starts `streamlit run app.py`.
- Forwards port `8501` and opens a browser preview.
- Pre-installs the Python + Pylance VS Code extensions.

---

## 🎛️ Customization

| What to change | Where | How |
|---|---|---|
| LLM model | `backend.py` | Edit `model=` in `ChatGroq(...)` |
| Temperature | `backend.py` | Add `temperature=0.7` to `ChatGroq(...)` |
| System prompt | `backend.py` → `chat_node` | Edit the `SystemMessage` content |
| App title | `app.py` | `st.set_page_config(page_title=...)` |
| Welcome message | `app.py` | Edit the banner markdown |
| Chat input placeholder | `app.py` | `st.chat_input("...")` |
| Max search results | `backend.py` | `TavilySearch(max_results=...)` |
| MCP server URL | `backend.py` → `MultiServerMCPClient` | Swap or add MCP endpoints |

---

## 🐛 Troubleshooting

**Missing API key error**
→ Make sure both `GROQ_API_KEY` and `TAVILY_API_KEY` exist in `.env` or Streamlit Secrets.

**MCP tools not loading**
→ Check internet access; the MCP server is a remote HTTP endpoint. The app falls back gracefully if it fails.

**Dependencies missing**
→ Run `pip install -r requirements.txt` with your virtual environment activated.

**Old chat history showing up**
→ Delete the local SQLite files (`bodhanai`, `bodhanai-shm`, `bodhanai-wal`) to start fresh.

**App doesn't open automatically**
→ Navigate to `http://localhost:8501` manually.

---

## 🚧 Current Limitations

- No user authentication or multi-user support
- No file or image upload
- No RAG / vector database integration
- No UI controls for model or temperature selection
- No chat export or delete-thread button
- Local SQLite storage — not suitable for multi-machine or cloud-native deployments as-is
- No automated test suite

---

## 👤 Author

**Harsh Raj** — IIT Mandi '29
[GitHub @HarshRaj4343](https://github.com/HarshRaj4343)

---

<p align="center">Built with ❤️ using Streamlit, LangGraph, and Groq</p>
