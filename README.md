# Bodha - Professional Chatbot

A professional chatbot application built with Streamlit and LangGraph, powered by HuggingFace language models.

## Features

- Interactive chat interface using Streamlit
- State management with LangGraph
- HuggingFace LLM integration
- Persistent chat history
- Professional UI with custom styling

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone this repository:

```bash
git clone <repository-url>
cd bodha
```

2. Create and activate a virtual environment:

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root (see `.env.example` if provided):

```bash
# Add your HuggingFace API key
HUGGINGFACEHUB_API_TOKEN=your_token_here
```

## Usage

Run the application with Streamlit:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Project Structure

```
bodha/
├── app.py              # Streamlit frontend application
├── backend.py          # LangGraph workflow and LLM integration
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── .env               # Environment variables (not committed)
```

## Components

### app.py

- Streamlit interface
- Chat message rendering
- Session state management
- Custom CSS styling

### backend.py

- LangGraph state graph setup
- HuggingFace LLM configuration
- Chat node implementation
- Message history management

## Dependencies

- **streamlit**: Web app framework
- **langchain-core**: Core LangChain utilities
- **langgraph**: Graph-based workflow engine
- **langchain-huggingface**: HuggingFace integration
- **python-dotenv**: Environment variable management

## Environment Variables

- `HUGGINGFACEHUB_API_TOKEN`: Your HuggingFace API token (required)

## Author

Harsh
