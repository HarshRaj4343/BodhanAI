# BodhanAI - Professional Chatbot

BodhanAI is a Streamlit chatbot application with a LangGraph-powered backend, Groq-hosted language model responses, streaming chat output, and persistent conversation state stored through SQLite checkpoints.

The app is designed as a clean personal/workbench chatbot: open it in the browser, start a conversation, create new chats, revisit recent threads, and keep chat history across app reloads.

## Table Of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running The App](#running-the-app)
- [Using BodhanAI](#using-bodhanai)
- [Data And Persistence](#data-and-persistence)
- [File Details](#file-details)
- [Deployment Notes](#deployment-notes)
- [Customization Guide](#customization-guide)
- [Troubleshooting](#troubleshooting)
- [Current Limitations](#current-limitations)
- [Author](#author)

## Features

- Browser-based chatbot interface built with Streamlit.
- Chatbot name and page title set to `BodhanAI`.
- Clean top-left brand header rendered with custom CSS.
- Welcome banner that appears before the first message.
- Sidebar workbench for chat controls.
- `New Chat` button for starting a fresh conversation thread.
- Recent conversation list in the sidebar.
- Unique thread IDs generated with Python `uuid`.
- Conversation messages stored in Streamlit session state for immediate UI rendering.
- User messages displayed with Streamlit chat bubbles.
- Assistant messages displayed with Streamlit chat bubbles.
- Prompt input powered by `st.chat_input`.
- Streaming assistant response display using `st.write_stream`.
- LangGraph workflow for backend conversation orchestration.
- Typed chat state using `TypedDict`.
- Message accumulation with LangGraph's `add_messages` reducer.
- System prompt that identifies the assistant as BodhanAI.
- Concise assistant behavior configured through the system message.
- Groq LLM integration through `langchain-groq`.
- Current model: `openai/gpt-oss-120b`.
- Current temperature: `0.7`.
- Local `.env` configuration support through `python-dotenv`.
- Streamlit Cloud configuration support through `st.secrets`.
- Graceful stop with a visible Streamlit error when the API key is missing.
- SQLite-backed checkpointing through `langgraph-checkpoint-sqlite`.
- Persistent conversation memory stored in the local `bodhanai` SQLite database file.
- SQLite write-ahead-log support files are ignored by Git.
- Automatic retrieval of saved conversation threads at startup.
- Conversation title generation through the same Groq model.
- Sidebar titles are generated as short conversation summaries.
- Title-generation prompt enforces concise, title-case labels.
- Dev Container configuration for Codespaces or compatible VS Code environments.
- Port `8501` forwarding configured for Streamlit.
- Python virtual environment, cache, logs, `.env`, and local database files ignored by Git.

## How It Works

At a high level, BodhanAI has two layers:

1. `app.py` handles the Streamlit user interface.
2. `backend.py` builds and exposes the LangGraph workflow.

When a user submits a prompt:

1. Streamlit captures the text from `st.chat_input`.
2. The user message is appended to `st.session_state.messages`.
3. The app streams a response from the LangGraph workflow.
4. LangGraph sends the conversation to the Groq chat model.
5. The assistant response streams back into the UI.
6. The final assistant response is appended to session state.
7. The app reruns so the latest conversation state is displayed.
8. LangGraph checkpointing stores thread state in SQLite.

The backend graph is intentionally simple:

```text
START -> Chat Node -> END
```

The single chat node adds BodhanAI's system message to the conversation, invokes the configured Groq model, and returns the model response as the next assistant message.

## Tech Stack

- **Python**: Main programming language.
- **Streamlit**: Web app framework and chat UI.
- **LangGraph**: Conversation workflow/state graph.
- **LangChain Core**: Message classes and shared LangChain primitives.
- **LangChain Groq**: Groq model integration.
- **Groq**: Hosted LLM provider.
- **SQLite**: Local persistent checkpoint storage.
- **python-dotenv**: Loads local environment variables from `.env`.
- **Dev Containers**: Optional Codespaces/VS Code development environment.

## Project Structure

```text
bodhanai/
|-- app.py                         # Streamlit frontend application
|-- backend.py                     # LangGraph workflow and Groq integration
|-- requirements.txt               # Python package dependencies
|-- README.md                      # Project documentation
|-- .env.example                   # Example environment file
|-- .env                           # Local secrets file, ignored by Git
|-- .gitignore                     # Ignored files and generated artifacts
|-- .devcontainer/
|   `-- devcontainer.json          # Optional dev container configuration
|-- bodhanai                       # Local SQLite checkpoint database, ignored by Git
|-- bodhanai-shm                   # SQLite shared-memory file, ignored by Git
`-- bodhanai-wal                   # SQLite write-ahead-log file, ignored by Git
```

## Requirements

- Python 3.8 or higher.
- `pip`.
- A valid Groq API key.
- Internet access when installing dependencies.
- Internet access at runtime so the app can call the Groq API.

The project dependencies are listed in `requirements.txt`:

```text
streamlit>=1.28.0
langchain-core>=0.1.0
langgraph>=0.0.50
langchain-huggingface>=0.0.1
python-dotenv>=1.0.0
langchain-groq>=0.0.1
langgraph-checkpoint-sqlite
```

Note: the current application code uses Groq for chat generation. `langchain-huggingface` is listed in the dependency file but is not used by the current `app.py` or `backend.py` implementation.

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd bodhanai
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

BodhanAI requires a Groq API key named `GROQ_API_KEY`.

For local development, create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

The backend loads this key with:

```python
os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
```

That means the key can come from either:

- A local `.env` file.
- A shell environment variable.
- Streamlit Secrets when deployed.

For Streamlit Cloud, add this secret in the app settings:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

If the key is missing, the app shows:

```text
API key not found. Please add GROQ_API_KEY to Streamlit Secrets.
```

and then stops execution with `st.stop()`.

## Running The App

Start the Streamlit server:

```bash
streamlit run app.py
```

By default, the app opens at:

```text
http://localhost:8501
```

## Using BodhanAI

1. Open the Streamlit app in your browser.
2. Type a message into the chat input.
3. Watch the assistant response stream into the page.
4. Continue the conversation in the same thread.
5. Use `New Chat` in the sidebar to create a fresh thread.
6. Use `Recents` in the sidebar to reopen previous conversations.

The initial empty state shows the welcome message:

```text
Ready to dive in?
```

The chat input placeholder is:

```text
Ask Anything.....
```

## Data And Persistence

BodhanAI uses LangGraph's SQLite checkpointer:

```python
conn = sqlite3.connect(database="bodhanai", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)
```

This creates local SQLite files:

- `bodhanai`
- `bodhanai-shm`
- `bodhanai-wal`

These files store checkpointed graph state, including conversation state by thread ID. They are intentionally ignored by Git so private chat history does not get committed.

Thread behavior:

- Every new chat receives a UUID thread ID.
- The current thread ID is stored in Streamlit session state.
- The LangGraph config passes the active thread ID through `configurable.thread_id`.
- Saved threads are loaded through `checkpointer.list(None)`.
- When a recent thread is selected, its stored messages are loaded back into the chat UI.

## File Details

### `app.py`

`app.py` is the Streamlit frontend. It is responsible for:

- Setting the browser page title.
- Rendering custom CSS.
- Displaying the `BodhanAI` brand header.
- Showing the welcome banner.
- Managing Streamlit session state.
- Creating new thread IDs.
- Resetting chats.
- Adding threads to the local recents list.
- Loading saved conversations from the backend workflow state.
- Rendering previous messages.
- Capturing user input.
- Streaming assistant responses.
- Triggering reruns after each assistant response.

Important UI state keys:

- `messages`: list of rendered chat messages.
- `thread_id`: active conversation thread ID.
- `chat_threads`: known conversation threads.

### `backend.py`

`backend.py` is the model and workflow layer. It is responsible for:

- Loading environment variables.
- Reading `GROQ_API_KEY`.
- Initializing the Groq chat model.
- Generating conversation titles.
- Defining the LangGraph chat state.
- Creating BodhanAI's system prompt.
- Invoking the LLM.
- Connecting to SQLite.
- Creating the LangGraph checkpoint saver.
- Building the graph.
- Compiling the workflow.
- Retrieving all known threads.

Current LLM configuration:

```python
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=groq_api_key,
    temperature=0.7
)
```

Current assistant system message:

```text
You are a helpful and concise chatbot. Your name is BodhanAI. Provide direct, clear answers without overthinking or verbose explanations.
```

### `get_model_title`

`get_model_title` asks the LLM to summarize a conversation into a short title.

The title prompt asks for:

- Only the title.
- Maximum 6 words.
- Preferably 2-5 words.
- Main topic, intent, or problem.
- No quotation marks.
- No punctuation.
- No emojis.
- No prefixes like `Title:`.
- Title case.
- Specific wording instead of generic labels.

### `.gitignore`

The ignore file excludes:

- Virtual environments.
- Python caches.
- Build artifacts.
- Environment files.
- IDE files.
- Streamlit config folders.
- Logs.
- Local SQLite database files generated by BodhanAI.

### `.devcontainer/devcontainer.json`

The dev container:

- Uses a Python 3.11 Bookworm image.
- Installs dependencies from `requirements.txt`.
- Installs Streamlit.
- Starts the app automatically with `streamlit run app.py`.
- Forwards port `8501`.
- Opens the forwarded app preview automatically where supported.
- Installs the Python and Pylance VS Code extensions.

## Deployment Notes

### Streamlit Cloud

1. Push the project to a Git repository.
2. Create a new Streamlit app from the repository.
3. Set the app entry point to `app.py`.
4. Add `GROQ_API_KEY` in Streamlit Secrets.
5. Deploy.

### Codespaces Or Dev Containers

If opened in an environment that supports Dev Containers, the included config can install requirements and start Streamlit automatically.

The app is configured to use port:

```text
8501
```

## Customization Guide

Change the model in `backend.py`:

```python
model="openai/gpt-oss-120b"
```

Adjust response creativity in `backend.py`:

```python
temperature=0.7
```

Change the assistant behavior by editing the `SystemMessage` in `chat_node`.

Change the browser page title in `app.py`:

```python
st.set_page_config(page_title="BodhanAI")
```

Change the visible brand text in `app.py`:

```python
st.markdown('<div class="company-name">BodhanAI</div>', unsafe_allow_html=True)
```

Change the empty-state welcome message in `app.py`:

```python
st.markdown('<div class="banner-name">Ready to dive in?</div>', unsafe_allow_html=True)
```

Change the chat input placeholder in `app.py`:

```python
prompt = st.chat_input("Ask Anything.....")
```

Change the SQLite database file name in `backend.py`:

```python
sqlite3.connect(database="bodhanai", check_same_thread=False)
```

If the database name changes, update `.gitignore` so generated SQLite files are still ignored.

## Troubleshooting

### Missing API Key

If the app stops with an API key error, make sure `GROQ_API_KEY` exists in one of these places:

- `.env`
- Your shell environment.
- Streamlit Secrets.

### Dependencies Not Found

Reinstall dependencies:

```bash
pip install -r requirements.txt
```

Make sure your virtual environment is activated before running Streamlit.

### Old Chat History Appears

The local SQLite files store conversation checkpoints. Remove or rename these local files if you want a completely fresh local history:

```text
bodhanai
bodhanai-shm
bodhanai-wal
```

### Streamlit Does Not Open Automatically

Open the local URL manually:

```text
http://localhost:8501
```

### Recents Look Unexpected

The app retrieves saved checkpoint threads from SQLite and displays them in the sidebar. Conversation titles are generated by the LLM from the currently available message history.

## Current Limitations

- No user authentication.
- No file upload feature.
- No image input feature.
- No retrieval-augmented generation pipeline.
- No vector database.
- No external tool calling.
- No admin dashboard.
- No chat export button.
- No delete-thread button.
- No model selector in the UI.
- No temperature control in the UI.
- No automated test suite currently included.
- Local chat history is stored on the machine running the app.

## Author

Harsh
