import chromadb
import os

print("🚀 Script started! Connecting to Database...") # 실행 확인용

# 경로 설정 확인
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma")
COLLECTION_NAME = "nci_course_chunks"

def count_keyword(keyword):
    print(f"📂 Looking into directory: {CHROMA_DIR}") # 경로 확인용
    
    try:
        # DB 연결 시도 (여기서 멈춘다면 다른 프로세스가 DB를 사용 중인 것)
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        col = client.get_collection(COLLECTION_NAME)
        
        all_data = col.get()
        documents = all_data['documents']
        
        count = sum(1 for doc in documents if keyword.lower() in doc.lower())
        
        print("\n" + "="*40)
        print(f"🔍 Keyword Check: '{keyword}'")
        print(f"✅ Total Chunks: {len(documents)}")
        print(f"✅ Found Chunks: {count}")
        print("="*40)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    count_keyword("career")