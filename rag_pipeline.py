from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FastEmbedEmbeddings

load_dotenv()

# FastEmbedEmbeddings is ONNX-based — no PyTorch/sentence-transformers needed
embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def doc_loader(file):
    loader = PyPDFLoader(file)
    return loader.load()

def doc_splitter(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(documents)

def embedder_vs(chunks):
    return FAISS.from_documents(chunks, embeddings)
