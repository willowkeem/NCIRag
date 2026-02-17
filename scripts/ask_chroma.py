import os
import chromadb
from sentence_transformers import SentenceTransformer

# -----------------------------
# 1. configuration (keep consistent with build_chroma.py)
# -----------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma")
COLLECTION_NAME = "nci_course_chunks" 

TOP_K = 3 # set the number of relevant chunks to retrieve
PREVIEW_CHARS = 500 # Max characters to display

def main():
    # Load emnedding model
    print("🤖 1. Local embedding model loading...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Database connection
    print(f"📂 2. Chroma DB connection: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    try:
        col = client.get_collection(COLLECTION_NAME)
    except Exception as e:
        print(f"❌ Error: Collection not found. Did you run build_chroma.py first?\n{e}")
        return

    print("\n✅ Ready! Enter your question and I'll find the most similar question.")
    print("Type 'exit' or 'quit' to terminate.\n")

    while True:
        try:
            query = input("Enter your question (Q)> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # Convert user's question to a number
        q_emb = model.encode([query], normalize_embeddings=True).tolist()[0]

        # Find the most similar chunks in the database
        res = col.query(
            query_embeddings=[q_emb],
            n_results=TOP_K,
            include=["documents", "metadatas", "distances"],
        )

        ids = res["ids"][0]
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]

        print(f"\n🔍 Found the top {TOP_K} most relevant pieces of information:\n")
        for i, (cid, doc, md, dist) in enumerate(zip(ids, docs, metas, dists), start=1):
            title = md.get("title", "No Title")
            label = md.get("label", "No Label")
            url = md.get("source_url", "No URL")

            print("=" * 60)
            print(f"[{i}] {title} ({label})")
            print(f"📍 Similarity(Distance): {dist:.4f} (Lower is more accurate)")
            print(f"🔗 Source: {url}")
            print("-" * 60)
            
            # Print text content
            print(doc[:PREVIEW_CHARS] + ("..." if len(doc) > PREVIEW_CHARS else ""))
            print("=" * 60 + "\n")

if __name__ == "__main__":
    main()