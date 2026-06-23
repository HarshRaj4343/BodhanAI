<h1 align="center">
  <br>
  🧠 BodhanAI
  <br>
</h1>

<p align="center">
  <b>A tool-augmented, RAG-capable AI chatbot built with Streamlit + LangGraph + Groq</b>
  <br/>
  <i>PDF Q&A · Real-time web search · Live stock prices with human approval · Voice input · Date/time tools via MCP · Persistent memory</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangGraph-Workflow-green?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Groq-LLM-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/FAISS-RAG-purple?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/SQLite-Persistence-lightgrey?style=for-the-badge&logo=sqlite"/>
</p>

---

## ✨ What is BodhanAI?

BodhanAI is a fully-featured AI chatbot that goes far beyond basic Q&A. It runs in your browser, streams responses in real time, remembers your conversations across sessions, answers questions about PDFs you upload, and can autonomously call external tools — searching the web, fetching live stock prices (with a human-in-the-loop confirmation step), and querying date/time services — all through a clean Streamlit interface. You can also just talk to it: a built-in mic input transcribes your voice with Groq Whisper before sending it to the graph.

---

## 🚀 Features at a Glance

| Category | Capability |
|---|---|
| 💬 **Chat** | Streaming responses, multi-turn memory, chat bubbles |
| 📄 **PDF RAG** | Upload a PDF per conversation thread and ask questions about it |
| 🔍 **Web Search** | Live Tavily-powered search with answer synthesis |
| 📈 **Stock Prices** | Real-time quotes via Alpha Vantage, gated behind a human-approval step |
| 🛑 **Human-in-the-Loop** | LangGraph `interrupt`/`Command(resume=...)` pauses the graph to ask "yes/no" before risky tool calls |
| 🎙️ **Voice Input** | Record a question via the browser mic; transcribed with Groq Whisper (`whisper-large-v3`) |
| 🕐 **Date & Time** | Remote MCP tool server for date/time queries |
| 🐙 **GitHub Aware** | Pre-loaded with your GitHub username for repo-related questions |
| 🧵 **Multi-thread** | Multiple parallel conversations, each with its own memory and its own indexed PDF |
| 📝 **Auto Titles** | LLM-generated conversation titles in the sidebar |
| 💾 **Persistence** | SQLite-backed checkpoints survive app restarts |
| ⚡ **Async Core** | Fully async backend with a dedicated event loop thread |
| 🛠️ **Tool UI** | Live status box shows which tool is running while streaming |

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    app.py (Streamlit UI)                  │
│  Sidebar · PDF upload · Mic input · Chat bubbles · Stream │
└────────────────────────────┬─────────────────────────────┘
                             │ calls
┌────────────────────────────▼─────────────────────────────┐
│                  backend.py (LangGraph)                   │
│                                                           │
│   START ──► chat_node ──► route_after_chat                │
│                 ▲              │                          │
│                 │       (tool call requested)             │
│                 │              ▼                          │
│                 │         hitl_node ──interrupt()──► user │
│                 │              │ Command(goto=...)        │
│                 │              ▼                          │
│                 └─────────  ToolNode  ◄────────────────── │
│   Tools: TavilySearch · get_stock_price · rag_tool · MCP  │
└────────────────────────────┬─────────────────────────────┘
                             │ checkpoints
┌────────────────────────────▼─────────────────────────────┐
│             SQLite  (AsyncSqliteSaver)                    │
│       messages  ·  thread IDs  ·  chat_titles            │
└──────────────────────────────────────────────────────────┘

                  Side path: PDF upload
        sidebar ──► ingest_pdf() ──► FAISS + FastEmbed
                         (per-thread retriever, in-memory)
```

**Graph flow:**

- Every user message enters `chat_node`, where the LLM (running via Groq) decides whether to call a tool or reply directly (`route_after_chat`).
- If a tool call was requested, control passes through `hitl_node` first. For `get_stock_price` specifically, `hitl_node` calls `interrupt()` and pauses the whole graph until the UI sends back a `Command(resume="yes"/"no")`. All other tool calls pass straight through.
- `ToolNode` executes the approved tool(s) and loops back to `chat_node`.
- The final assistant message streams to the UI.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Groq — `openai/gpt-oss-120b` (served via Groq's OpenAI-compatible endpoint) |
| Orchestration | LangGraph (async `StateGraph`, `interrupt`/`Command` for HITL) |
| Tool: Web Search | LangChain Tavily (`TavilySearch`) |
| Tool: Stock Prices | Alpha Vantage API via `aiohttp` |
| Tool: PDF RAG | `PyPDFLoader` + `RecursiveCharacterTextSplitter` + FAISS + `FastEmbedEmbeddings` (`BAAI/bge-small-en-v1.5`) |
| Tool: Date & Time | Remote MCP server via `langchain-mcp-adapters` |
| Voice Input | Groq Whisper (`whisper-large-v3`) via the `groq` SDK |
| Persistence | SQLite via `aiosqlite` + `AsyncSqliteSaver` |
| Env Config | `python-dotenv` + Streamlit Secrets |
| Dev Env | Dev Containers (Codespaces / VS Code) |

---

## 📁 Project Structure

```
bodhanai/
├── app.py                     # Streamlit UI — chat, sidebar, PDF upload, mic input, streaming
├── backend.py                 # LangGraph graph, tools, HITL node, async loop, SQLite
├── rag_pipeline.py            # PDF loading, chunking, FAISS + FastEmbed indexing
├── requirements.txt           # Python dependencies
├── README.md                  # You are here
├── .env.example               # Template for local secrets
├── .env                       # Your actual secrets (git-ignored)
├── .gitignore                 # Ignores venv, cache, .env, SQLite files
├── Procfile                   # Heroku-style process declaration
├── langgraph.png              # Auto-generated graph diagram (written at import time)
├── .devcontainer/
│   └── devcontainer.json      # Codespaces / VS Code dev container config
├── .streamlit/
│   └── config.toml            # Streamlit theme/config
├── bodhanai                   # SQLite database (git-ignored)
├── bodhanai-shm               # SQLite shared memory (git-ignored)
└── bodhanai-wal               # SQLite write-ahead log (git-ignored)
```

---

## ⚙️ Installation

### 1 — Clone the repo

```bash
git clone https://github.com/HarshRaj4343/BodhanAI.git
cd BodhanAI
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

> **Note:** PDF RAG pulls in FAISS, FastEmbed (ONNX) and PyTorch-adjacent libraries, so the first install can take a few minutes.

---

## 🔑 Configuration

BodhanAI needs four API keys. Create a `.env` file in the project root (you can copy `.env.example` as a starting point):

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
GROQ_SPEECH_API_KEY=your_groq_speech_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
```

| Key | Used for | Required? |
|---|---|---|
| `GROQ_API_KEY` | Main chat LLM (`ChatGroq`) | ✅ Yes — app raises on startup if missing |
| `TAVILY_API_KEY` | Web search tool | ✅ Yes — app raises on startup if missing |
| `GROQ_SPEECH_API_KEY` | Whisper transcription for voice input | ✅ Yes for mic input (can reuse the same value as `GROQ_API_KEY`) |
| `ALPHA_VANTAGE_API_KEY` | Live stock price lookups | ✅ Yes for the stock price tool |

> **Streamlit Cloud?** Add these as secrets under **App Settings → Secrets** in TOML format:
> ```toml
> GROQ_API_KEY = "your_groq_api_key_here"
> TAVILY_API_KEY = "your_tavily_api_key_here"
> GROQ_SPEECH_API_KEY = "your_groq_speech_api_key_here"
> ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_api_key_here"
> ```

If `GROQ_API_KEY` or `TAVILY_API_KEY` is missing, the app shows a clear error and stops safely at import time.

---

## ▶️ Running the App

```bash
streamlit run app.py
```

Opens at: **http://localhost:8501**

---

## 🧩 Tools & Capabilities

### 📄 PDF RAG
Upload a PDF from the sidebar for the current conversation thread. BodhanAI loads it with `PyPDFLoader`, splits it into overlapping chunks, embeds them with the ONNX-based `FastEmbedEmbeddings` (no PyTorch download needed), and indexes them in an in-memory FAISS store scoped to that thread. Ask questions about the document and the `rag_tool` retrieves the most relevant chunks (with page numbers) for the LLM to answer from.

```
"Summarize the key findings in the uploaded PDF"
"What does the resume say about previous internships?"
```

### 🔍 Web Search — Tavily
BodhanAI can search the live web to answer questions about current events, recent news, or anything beyond its training data. Powered by `TavilySearch`.

### 📈 Stock Price Lookup — with Human-in-the-Loop
Ask about any stock ticker and BodhanAI prepares to fetch the latest price from the Alpha Vantage API. Before the call actually runs, the graph **pauses** via `hitl_node` and asks you to confirm:

```
"What is the current price of AAPL?"
→ "Are you sure you want to fetch the stock price for AAPL? Please answer yes or no."
```

Click **✅ Yes** to proceed or **❌ No** to cancel — the graph resumes from exactly where it paused using `Command(resume=...)`.

### 🎙️ Voice Input
Record a question with the browser mic (`st.audio_input`). The audio is transcribed with Groq's `whisper-large-v3` model and sent into the same chat pipeline as typed messages.

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
2. (Optional) Upload a PDF from the sidebar to enable document Q&A for this chat.
3. Type a message in the chat input, or record one with the mic.
4. Watch the response stream word by word. If a stock price lookup is requested, confirm or cancel it when prompted.
5. Click **New Chat** in the sidebar to start a fresh conversation (with its own PDF context).
6. Browse and reopen previous conversations from **Recents** in the sidebar — each one is titled automatically by the LLM.

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

> **Note:** Indexed PDFs (FAISS retrievers) live **in memory only** and are keyed by thread ID — they are rebuilt by re-uploading the PDF if the app process restarts.

---

## 🔄 Async Architecture

BodhanAI runs a **dedicated background event loop** on a daemon thread so that async LangGraph and tool calls work seamlessly inside Streamlit's synchronous execution model:

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
4. Add all four API keys in **App Settings → Secrets**.
5. Deploy. ✅

### Heroku / Procfile-based platforms

The repo includes a `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```
Set the API keys as config vars/environment variables on your platform, then deploy as you normally would for a Python app.

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
| Which tools require human approval | `backend.py` → `hitl_node` | Edit the `stock_calls` filter to add/remove tool names |
| Embedding model | `rag_pipeline.py` | Edit `model_name=` in `FastEmbedEmbeddings(...)` |
| Chunk size / overlap | `rag_pipeline.py` | Edit `RecursiveCharacterTextSplitter(...)` args |
| Retriever `k` | `backend.py` → `ingest_pdf` | Edit `search_kwargs={"k": ...}` |
| App title | `app.py` | `st.set_page_config(page_title=...)` |
| Welcome message | `app.py` | Edit the banner markdown |
| Max search results | `backend.py` | `TavilySearch(max_results=...)` |
| MCP server URL | `backend.py` → `MultiServerMCPClient` | Swap or add MCP endpoints |

---

## 🐛 Troubleshooting

**Missing API key error**
→ Make sure all four keys exist in `.env` or Streamlit Secrets. See the [Configuration](#-configuration) section.

**MCP tools not loading**
→ Check internet access; the MCP server is a remote HTTP endpoint. The app falls back gracefully if it fails to connect.

**PDF upload doesn't seem to do anything / "No document has been indexed"**
→ Wait for the "✅ PDF indexed" confirmation in the sidebar before asking questions, and make sure you're asking in the same chat thread you uploaded to — indexed PDFs are scoped per-thread and live in memory only.

**Stock price requests seem stuck**
→ Look for a confirmation prompt above the chat input — `get_stock_price` calls pause the graph until you click ✅ Yes or ❌ No.

**Voice input fails to transcribe**
→ Confirm `GROQ_SPEECH_API_KEY` is set. This can be the same value as your main `GROQ_API_KEY`.

**Dependencies missing**
→ Run `pip install -r requirements.txt` with your virtual environment activated.

**Old chat history showing up**
→ Delete the local SQLite files (`bodhanai`, `bodhanai-shm`, `bodhanai-wal`) to start fresh.

**App doesn't open automatically**
→ Navigate to `http://localhost:8501` manually.

---

## 🚧 Current Limitations

- No user authentication or multi-user support
- No image upload (PDF only)
- Human-in-the-loop approval is currently wired up only for stock price lookups
- Indexed PDFs live in memory and are lost on process restart (no persistent vector store)
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
