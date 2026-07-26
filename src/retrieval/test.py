from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PATH = "./chroma_db"

def test_retrieval():
    print("Loading embedding model...")
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("Connecting to vector database...")
    # Load the existing database
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_model)
    
    # The question we want to ask our database
    query = "What are the rules regarding KYC and income verification for credit?"
    print(f"\nSearching for: '{query}'\n")
    
    # Perform semantic similarity search (k=2 means return the top 2 closest chunks)
    results = db.similarity_search(query, k=2)
    
    if not results:
        print("No results found. Did you run ingest.py with a PDF in the data/ folder?")
        return
        
    print("--- TOP MATCHES ---")
    for i, result in enumerate(results):
        print(f"\nMatch {i+1}:")
        print(result.page_content)
        print(f"Source: {result.metadata.get('source', 'Unknown')}")

if __name__ == "__main__":
    test_retrieval()