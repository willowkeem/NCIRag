import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

# 1. Path configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHUNKS_PATH = os.path.join(BASE_DIR, "data", "chunks", "chunks.jsonl")
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma")
COLLECTION_NAME = "nci_course_chunks"

os.makedirs(CHROMA_DIR, exist_ok=True)

def read_jsonl(path):
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def main():
    if not os.path.exists(CHUNKS_PATH):
        print("❌ Error: data/chunks/chunks.jsonl not found!")
        return

    print("🤖 1. Loading local embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"📂 2. Connecting to Chroma DB: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Remove existing data if present (Initialize)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"🧹 Deleted existing '{COLLECTION_NAME}' collection.")
    except:
        pass

    # Create collection
    col = client.get_or_create_collection(name=COLLECTION_NAME)

    print("🚀 3. Start data indexing...")
    
    ids, docs, metas = [], [], []
    total = 0

    for chunk in read_jsonl(CHUNKS_PATH):
        text = chunk.get("text", "").strip()
        if not text:
            continue

        ids.append(chunk.get("chunk_id"))
        docs.append(text)
        metas.append({
            "source_url": chunk.get("source_url", ""),
            "title": chunk.get("title", ""),
            "label": chunk.get("label", "")
        })

        # Save in batches of 100
        if len(ids) >= 100:
            embs = model.encode(docs, normalize_embeddings=True).tolist()
            col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
            total += len(ids)
            print(f"✅ {total} records saves successfully...")
            ids, docs, metas = [], [], []

    # Processing remaining data
    if ids:
        embs = model.encode(docs, normalize_embeddings=True).tolist()
        col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        total += len(ids)

    print(f"\n✨ A total of {total} records have been successfully indexed.")

if __name__ == "__main__":
    main()
