import os
from pathlib import Path
import sys
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
import chromadb

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# CHANGED: path sekarang nunjuk ke chroma_db di rumi-rag/backend/,
# karena eval folder ini hidup di luar project root (sejajar sama rumi-rag/)
CHROMA_DB_PATH = Path(__file__).resolve().parent.parent / "rumi-rag" / "backend" / "chroma_db"

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    task_type="RETRIEVAL_QUERY", # ADDED: jangan andelin default bawaan langchain buat embed_query,
                                 # soalnya ada bug tercatat (GitHub issue #1299) yang bikin default-nya
                                 # kadang gak ke-apply pas task_type gak di-set eksplisit   
)

chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))

vectorstore = Chroma(
    client=chroma_client,
    collection_name="mpasi_kb",
    embedding_function=embeddings,
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

if __name__ == "__main__":
    test_query = "resep MPASI untuk bayi 6 bulan"
    results = retriever.invoke(test_query)
    for doc in results:
        print(f"[Sumber: {doc.metadata.get('source', 'unknown')}]")
        print(f"  {doc.page_content[:100]}...")
        print()