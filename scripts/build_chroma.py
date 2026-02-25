import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Path Configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) 
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..")) 

# The path you confirmed via 'ls -l'
MANIFEST_PATH = "/Users/wuyeonkim/Desktop/NCIRag/data/raw/manifest.jsonl"
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "html")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "data", "chroma")
COLLECTION_NAME = "nci_course_chunks"

def main():
    print(f"🔍 [STEP 1] Checking manifest at: {MANIFEST_PATH}")
    if not os.path.exists(MANIFEST_PATH):
        print(f"❌ ERROR: Manifest file NOT FOUND!")
        return

    # Diagnostic: Check HTML folder content
    print(f"🔍 [STEP 2] Checking HTML folder at: {RAW_DATA_DIR}")
    if os.path.exists(RAW_DATA_DIR):
        files_in_folder = os.listdir(RAW_DATA_DIR)
        print(f"📂 Found {len(files_in_folder)} files in 'html' folder.")
        if len(files_in_folder) > 0:
            print(f"📄 Sample file: {files_in_folder[0]}")
    else:
        print(f"❌ ERROR: HTML folder NOT FOUND at {RAW_DATA_DIR}!")

    # 2. Initialize Model & DB
    print("🤖 [STEP 3] Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"🧹 Cleaned existing collection.")
    except: pass
    col = client.get_or_create_collection(name=COLLECTION_NAME)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    print("🚀 [STEP 4] Start indexing...")
    ids, docs, metas = [], [], []
    total_chunks = 0
    file_count = 0

    with open(MANIFEST_PATH, "r", encoding="utf8") as f:
        for line in f:
            item = json.loads(line)
            filename = item.get("raw_filename")
            # Try both /html folder and parent folder as backup
            raw_path = os.path.join(RAW_DATA_DIR, filename)
            
            if not os.path.exists(raw_path):
                raw_path = os.path.join(PROJECT_ROOT, "data", "raw", filename)

            if not os.path.exists(raw_path):
                # Print only the first failure to avoid spamming
                if file_count == 0 and total_chunks == 0:
                    print(f"⚠️ Warning: Cannot find file '{filename}' at searched paths.")
                continue

            file_count += 1
            with open(raw_path, "r", encoding="utf8", errors='ignore') as rf:
                content = rf.read().strip()
            
            if not content: continue

            chunks = text_splitter.split_text(content)
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"{item['doc_id']}_v{i}"
                ids.append(chunk_id)
                docs.append(chunk_text)
                metas.append({"source_url": item.get("source_url"), "title": filename})

                if len(ids) >= 100:
                    embs = model.encode(docs, normalize_embeddings=True).tolist()
                    col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
                    total_chunks += len(ids)
                    print(f"✅ Indexed {total_chunks} chunks...")
                    ids, docs, metas = [], [], []

    if ids:
        embs = model.encode(docs, normalize_embeddings=True).tolist()
        col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        total_chunks += len(ids)

    print(f"\n✨ FINAL RESULT: Processed {file_count} files.")
    print(f"✨ Total chunks in DB: {total_chunks}")

if __name__ == "__main__":
    main()