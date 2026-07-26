import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration constants
DATA_DIR = "./data"
CHROMA_PATH = "./chroma_db"

def ingest_documents():
    print(f"Loading PDFs from {DATA_DIR}...")
    
    # 1. Load Documents
    loader = PyPDFDirectoryLoader(DATA_DIR)
    documents = loader.load()
    
    if not documents:
        print("No documents found! Please add PDF files to the data/ folder.")
        return

    print(f"Loaded {len(documents)} pages. Splitting into chunks...")

    # 2. Split Text into Chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks.")

    # 3. Initialize Embedding Model (Local & Free)
    print("Initializing embedding model...")
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. Create and Persist the Vector Database
    print("Saving to Chroma vector database...")
    
    # Clear out the old database if it exists so we start fresh
    if os.path.exists(CHROMA_PATH):
        import shutil
        shutil.rmtree(CHROMA_PATH)
        
    db = Chroma.from_documents(
        documents=chunks, 
        embedding=embedding_model, 
        persist_directory=CHROMA_PATH
    )
    
    print(f"Successfully saved {len(chunks)} chunks to {CHROMA_PATH}.")

if __name__ == "__main__":
    ingest_documents()