import os
from pathlib import Path
import memory as _memory

corpus_dir = Path("/Users/pankaj/Documents/EAG/s7/sandbox/corpus")

if not corpus_dir.exists():
    print("Corpus directory not found!")
    exit(1)

def chunk_text(text: str, size: int = 150, overlap: int = 30) -> list[str]:
    """Chunk by a smaller size to get more chunks (easily exceeding 50 items)
    and ensure precise retrieval windows."""
    words = text.split()
    if not words:
        return []
    chunks = []
    stride = max(1, size - overlap)
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + size]))
        if i + size >= len(words):
            break
        i += stride
    return chunks

_memory.clear()
print("Cleared prior index.")

indexed_count = 0
for child in sorted(corpus_dir.iterdir()):
    if not child.is_file() or not child.name.endswith(".md"):
        continue
    
    text = child.read_text(encoding="utf-8")
    source = f"sandbox:corpus/{child.name}"
    chunks = chunk_text(text, size=60, overlap=15)
    
    print(f"Indexing {child.name} — split into {len(chunks)} chunks...")
    run_id = "index-bulk"
    
    import time
    for i, chunk in enumerate(chunks):
        preview = chunk[:120].replace("\n", " ")
        descriptor = f"[{source} chunk {i+1}/{len(chunks)}] {preview}"
        
        # Respect upstream Gemini 15 RPM embedding rate limit
        time.sleep(4.2)
        
        _memory.add_fact(
            descriptor=descriptor,
            value={
                "chunk": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source": source,
            },
            source=source,
            run_id=run_id,
        )
        indexed_count += 1

print(f"\nSuccessfully indexed {indexed_count} chunks/items in the vector memory!")
