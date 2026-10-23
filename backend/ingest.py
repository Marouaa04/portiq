import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb

DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "documents")
DB_FOLDER = os.path.join(os.path.dirname(__file__), "chroma_db")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def read_pdf(filepath):
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def split_into_chunks(text, source_name):
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        if chunk.strip():
            chunks.append({"text": chunk, "source": source_name})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def build_database():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=DB_FOLDER)

    try:
        client.delete_collection("marologix_docs")
    except Exception:
        pass

    collection = client.create_collection("marologix_docs")
    all_chunks = []

    for filename in os.listdir(DOCS_FOLDER):
        if filename.endswith(".pdf"):
            filepath = os.path.join(DOCS_FOLDER, filename)
            print(f"Reading {filename}...")
            text = read_pdf(filepath)
            chunks = split_into_chunks(text, filename)
            all_chunks.extend(chunks)
            print(f"  {len(chunks)} chunks")

    print(f"Total: {len(all_chunks)} chunks")

    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        vectors = model.encode(texts).tolist()
        ids = [f"chunk_{i+j}" for j in range(len(batch))]
        metadatas = [{"source": c["source"]} for c in batch]
        collection.add(
            documents=texts,
            embeddings=vectors,
            metadatas=metadatas,
            ids=ids,
        )

    print(f"Done. {collection.count()} chunks stored.")


if __name__ == "__main__":
    build_database()