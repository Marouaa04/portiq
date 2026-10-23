import os
from dotenv import load_dotenv
from groq import Groq
from rag import search
from memory import load_history, add_message

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SYSTEM_PROMPT = (
    "You are MARO, an expert assistant specialized in Moroccan logistics, "
    "customs law, Incoterms 2020, and port operations. "
    "You have access to official documents: the Moroccan Customs Code 2026, "
    "Incoterms 2020 Guide, and ANP Port Report 2025. "
    "Always cite the source document when you answer. "
    "If the answer is not in the documents, say so clearly. "
    "Answer in the same language as the user question. "
    "Be precise, structured, and professional."
)


def chat(question):
    history = load_history()

    chunks = search(question, n_results=4)

    context = ""
    for chunk in chunks:
        context += "\nSource: " + chunk["source"] + "\n" + chunk["text"] + "\n---"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({
        "role": "user",
        "content": (
            "Here are relevant excerpts from the official documents:\n"
            + context
            + "\n\nMy question: " + question
        )
    })

    # Read from Streamlit secrets first, then .env
    try:
        import streamlit as st
        api_key = st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    except Exception:
        api_key = os.getenv("GROQ_API_KEY", "")

    groq_client = Groq(api_key=api_key)
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        max_tokens=1500,
    )

    answer = response.choices[0].message.content

    add_message(history, "user", question)
    add_message(history, "assistant", answer)

    return answer