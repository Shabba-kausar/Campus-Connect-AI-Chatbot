# ===============================
# MANUU AI Chatbot (RAG Version)
# ===============================

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os
try:
    from openai import OpenAI
except Exception:
    OpenAI = None
from dotenv import load_dotenv
from bot.openai_helper import get_bot_reply


# Load .env so OPENAI_API_KEY (if present) is available to the OpenAI client
load_dotenv()

# Ensure API key loaded from environment
OPENAI_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
if not OPENAI_KEY:
    raise RuntimeError('OPENAI_API_KEY not found. Please add it to your environment or .env file')
# Use new OpenAI client rather than setting openai.api_key globally
# The client will pick up the key from environment variables.

# Load embeddings and vector database (expects a local FAISS index directory 'manuu_vector_db')
embeddings = OpenAIEmbeddings(model=os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'))
# Try to load FAISS; if the local index is missing, fallback to numpy embeddings + sentence-transformers
FAISS_INDEX_DIR = "manuu_vector_db"
db = None
if os.path.isdir(FAISS_INDEX_DIR):
    try:
        db = FAISS.load_local(FAISS_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    except Exception:
        db = None

# Fallback resources (used if FAISS index not available)
EMB_FALLBACK = os.path.join(os.path.dirname(__file__), 'manuu_embeddings.npy')
CHUNKS_FALLBACK = os.path.join(os.path.dirname(__file__), 'manuu_chunks_index.txt')

def fallback_retrieve(query: str, k: int = 4):
    """Retrieve top-k chunks using local numpy embeddings and sentence-transformers."""
    try:
        import numpy as _np
        from sentence_transformers import SentenceTransformer

        if not os.path.exists(EMB_FALLBACK) or not os.path.exists(CHUNKS_FALLBACK):
            return []

        embeddings = _np.load(EMB_FALLBACK)
        with open(CHUNKS_FALLBACK, 'r', encoding='utf-8') as f:
            chunks = [line.strip() for line in f if line.strip()]

        model = SentenceTransformer(os.getenv('FALLBACK_EMB_MODEL', 'all-MiniLM-L6-v2'))
        q_emb = model.encode([query], convert_to_numpy=True)[0]
        # cosine similarity
        sims = (_np.dot(embeddings, q_emb) / (_np.linalg.norm(embeddings, axis=1) * _np.linalg.norm(q_emb) + 1e-8))
        topk_idx = sims.argsort()[-k:][::-1]
        return [chunks[i] for i in topk_idx]
    except Exception:
        return []


def manuu_chatbot(user_query: str) -> str:
    """
    Main chatbot function — retrieves relevant info from MANUU database
    and generates a ChatGPT-style structured answer.
    """

    # Step 1: Retrieve top 4 matching chunks
    context = ""
    if db is not None:
        try:
            docs = db.similarity_search(user_query, k=4)
            context = "\n\n".join([d.page_content for d in docs])
        except Exception:
            db = None

    if not context:
        # fallback retrieval
        top_chunks = fallback_retrieve(user_query, k=4)
        context = "\n\n".join(top_chunks)

    # Step 2: Build prompt with ChatGPT-like formatting instructions
    prompt = f"You are a helpful MANUU University assistant. Answer concisely using a heading and 2-5 bullet points. Use bold for important terms. If you cannot answer from the context, reply: 'I'm sorry, I don’t have updated information about that right now.'\n\nContext:\n{context}\n\nUser question: {user_query}\n\nAnswer:" 

    # Step 3: Use the centralized helper to generate the structured response. This
    # avoids direct usage of deprecated OpenAI ChatCompletion interfaces.
    try:
        reply = get_bot_reply(user_query, context=context)
        return reply
    except Exception as e:
        return f"[LLM error] {e}"
    return "I'm sorry, I don’t have updated information about that right now."


# Step 5: CLI interaction (terminal)
if __name__ == "__main__":
    print("\n🤖 MANUU AI Chatbot is ready! Type 'exit' to quit.\n")
    while True:
        q = input("Ask MANUU Chatbot: ")
        if q.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        ans = manuu_chatbot(q)
        print("\nAI Chatbot:", ans, "\n")
