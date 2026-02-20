import chromadb
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma")
COLLECTION_NAME = "nci_course_chunks"

def dump_data(keyword):
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_collection(COLLECTION_NAME)
    
    all_data = col.get()
    # 키워드가 포함된 데이터만 필터링
    career_chunks = [doc for doc in all_data['documents'] if keyword.lower() in doc.lower()]
    
    with open("career_debug_dump.txt", "w", encoding="utf-8") as f:
        for i, doc in enumerate(career_chunks):
            f.write(f"--- Chunk {i+1} ---\n")
            f.write(doc + "\n\n")
    
    print(f"✅ {len(career_chunks)} chunks saved to 'career_debug_dump.txt'. Open it and check!")

if __name__ == "__main__":
    dump_data("career")