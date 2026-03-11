from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

# ✅ Your MANUU data file
with open("manuu_chunks_index.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

# ✅ Split into clean chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", "?", "!", " "]
)
texts = splitter.split_text(raw_text)
docs = [Document(page_content=t) for t in texts]

# ✅ Create embeddings (offline, no API key required)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ✅ Create FAISS vector store
db = FAISS.from_documents(docs, embeddings)

# ✅ Save it for later use
db.save_local("manuu_vector_db")

print("✅ MANUU Embedding Database Created Successfully!")