import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from rag import ask

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    question: str
    api_key: Optional[str] = None


@app.get("/")
def root():
    return {"status": "MaroLogix backend running"}


@app.post("/ask")
def ask_question(body: Question):
    result = ask(body.question, api_key=body.api_key)
    return result