import os
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# 1. Load environment variables (API Key)
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Path Configuration (Moving up from 'scripts' to 'data')
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma")
COLLECTION_NAME = "nci_course_chunks"

# 3. Load Embedding Model
model_st = SentenceTransformer("all-MiniLM-L6-v2")

def get_context(query, top_k=3):
    """Search for relevant documents in local ChromaDB."""
    db_client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = db_client.get_collection(COLLECTION_NAME)
    
    q_emb = model_st.encode([query], normalize_embeddings=True).tolist()[0]
    results = col.query(query_embeddings=[q_emb], n_results=top_k)
    
    return results["documents"][0], results["metadatas"][0]

def generate_answer(query, contexts):
    """Generate a human-like answer using OpenAI GPT-4o based on context."""
    context_text = "\n\n".join(contexts)
    
    system_msg = (
        "You are an expert advisor for the National College of Ireland (NCI). "
        "Answer the user's question accurately based ONLY on the provided context. "
        "If the answer is not in the context, politely say you don't have that information."
    )
    
    user_msg = f"Context:\n{context_text}\n\nQuestion: {query}\n\nAnswer (in English):"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        temperature=0.2 # Keeping it factual
    )
    return response.choices[0].message.content

# 4. Main Chat Loop
if __name__ == "__main__":
    print("--- NCI AI Chatbot (GPT-4o Powered) ---")
    while True:
        query = input("\nQ> ").strip()
        if query.lower() in ["exit", "quit"]: break
        
# DEBUG START         
        print("Searching and generating answer...")
        docs, metas = get_context(query, top_k=5)

        print("\n" + "="*50)
        print("🔍 [DEBUG] Relevant data retrieved from ChromaDB (Top 5)")
        print("="*50)

        for i, (doc, meta) in enumerate(zip(docs, metas)):
            print(f"\n[{i+1}] Source: {meta.get('title', 'No Title')}")
            print(f"    URL: {meta.get('source_url', 'No URL')}")

            # Cleaning and previewing the first 300 characters
            clean_doc = doc.replace('\n', ' ').strip()
            print(f"    Content: {clean_doc[:300]}...") 
            print("-" * 30)
            
        print("="*50 + "\n")
# DEBUG END

        answer = generate_answer(query, docs)
        
        print(f"\nAI: {answer}")
        print("\n[Sources]")
        for m in metas:
            print(f"- {m['title']}: {m['source_url']}")