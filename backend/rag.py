import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DB_FOLDER = os.path.join(os.path.dirname(__file__), "chroma_db")

model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=DB_FOLDER)
collection = chroma_client.get_collection("marologix_docs")


def search(question, n_results=4):
    vector = model.encode([question]).tolist()
    results = collection.query(query_embeddings=vector, n_results=n_results)
    found = []
    for i in range(len(results["documents"][0])):
        found.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "distance": results["distances"][0][i],
        })
    return found


def ask(question, api_key=None):
    chunks = search(question)
    sources = list(set([c["source"] for c in chunks]))

    # Read from Streamlit secrets first, then .env
    try:
        import streamlit as st
        resolved_key = api_key or st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    except Exception:
        resolved_key = api_key or os.getenv("GROQ_API_KEY", "")

    if not resolved_key:
        return {
            "answer": "Clé API manquante. Ajoutez GROQ_API_KEY dans vos secrets Streamlit ou dans le fichier .env.",
            "sources": sources,
            "mode": "error"
        }

    context = ""
    for chunk in chunks:
        context += "\nSource: " + chunk["source"] + "\n" + chunk["text"] + "\n---"

    prompt = (
        "You are a Moroccan logistics and customs expert. "
        "Answer using ONLY the documents provided below. "
        "If the answer is not in the documents, say so clearly. "
        "Always mention which source your answer comes from. "
        "Answer in the same language as the question.\n\n"
        "DOCUMENTS:\n" + context + "\n\nQUESTION: " + question
    )

    groq_client = Groq(api_key=resolved_key)
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )

    answer = response.choices[0].message.content
    return {"answer": answer, "sources": sources, "mode": "live"}