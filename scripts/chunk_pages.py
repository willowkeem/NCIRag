import os, json, re, hashlib

# 1. Path setup (Set relative to current directory to prevent path errors)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
PAGES_IN = os.path.join(CLEAN_DIR, "pages.jsonl")

CHUNK_DIR = os.path.join(BASE_DIR, "data", "chunks")
CHUNKS_OUT = os.path.join(CHUNK_DIR, "chunks.jsonl")
os.makedirs(CHUNK_DIR, exist_ok=True)

# 2. Chunking configuration 
SOFT_MAX_TOKENS = 800  # Recommended max length
HARD_MAX_TOKENS = 1000 # Absloute max length

def read_jsonl(path):
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def est_tokens(text: str) -> int:
    """Simple token count estimation (word count * 1.4)"""
    words = len((text or "").split())
    return int(words * 1.4)

def generate_chunk_id(doc_id: str, idx: int) -> str:
    """Generate unique chunk IDs"""
    base = f"{doc_id}_{idx}"
    h = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
    return f"{doc_id}_{h}"

def write_chunk(out, doc, label, text, idx):
    """Write chunk data to file"""
    text = (text or "").strip()
    if not text or len(text) < 20: # Ignore text that is too short
        return

    chunk_data = {
        "chunk_id": generate_chunk_id(doc.get("doc_id", "unknown"), idx),
        "doc_id": doc.get("doc_id"),
        "source_url": doc.get("source_url"),
        "title": doc.get("title"),
        "label": label,
        "text": text,
        "metadata": {
            "est_tokens": est_tokens(text),
            "retrieved_at": doc.get("retrieved_at")
        }
    }
    out.write(json.dumps(chunk_data, ensure_ascii=False) + "\n")

def main():
    if not os.path.exists(PAGES_IN):
        print(f"Error: {PAGES_IN} not found. Run clean_pages.py first.")
        return

    print("Chunking NCI data...")
    idx_counter = 0
    with open(CHUNKS_OUT, "w", encoding="utf8") as out:
        for doc in read_jsonl(PAGES_IN):
            # 1) Metadata Chunk (Title and URL)
            title = doc.get("title", "NCI Course")
            write_chunk(out, doc, "Overview", f"Course Title: {title}\nSource: {doc.get('source_url')}", idx_counter)
            idx_counter += 1

            # 2) Section-based chunking (Using sections extracted from NCI clean_pages)
            for s in doc.get("sections", []):
                heading = s.get("heading", "Information")
                content = s.get("text", "")
                
                # Skip meaningless sections with no title (e.g., footers)
                if not heading and len(content) < 100:
                    continue

                full_section_text = f"[{heading}]\n{content}"
                
                # Split section into paragraph if content exceeds max length
                if est_tokens(full_section_text) > HARD_MAX_TOKENS:
                    paragraphs = content.split("\n")
                    buffer = []
                    for p in paragraphs:
                        buffer.append(p)
                        current_text = f"[{heading} (continued)]\n" + "\n".join(buffer)
                        if est_tokens(current_text) > SOFT_MAX_TOKENS:
                            write_chunk(out, doc, heading, current_text, idx_counter)
                            idx_counter += 1
                            buffer = []
                    if buffer:
                        write_chunk(out, doc, heading, f"[{heading} (continued)]\n" + "\n".join(buffer), idx_counter)
                        idx_counter += 1
                else:
                    write_chunk(out, doc, heading, full_section_text, idx_counter)
                    idx_counter += 1

    print(f"Success! Created chunks in: {CHUNKS_OUT}")

if __name__ == "__main__":
    main()