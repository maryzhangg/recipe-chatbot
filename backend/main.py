from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import datetime
import requests
import weaviate
from sentence_transformers import SentenceTransformer

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:1b"

client = weaviate.Client("http://localhost:8080")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

class ChatRequest(BaseModel):
    user_id: str
    message: str

def store_user_message(user_id, message, role):
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("INSERT INTO history (user_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
              (user_id, role, message, datetime.datetime.now()))
    conn.commit()
    conn.close()

def get_user_history(user_id):
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("SELECT role, message FROM history WHERE user_id=? ORDER BY timestamp ASC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": role, "content": msg} for role, msg in rows]

def search_pdf_chunks(query, top_k=3):
    query_vec = embedder.encode(query).tolist()
    result = client.query.get("PDFChunk", ["content", "page", "source"])\
                .with_near_vector({"vector": query_vec})\
                .with_limit(top_k)\
                .do()
    return [
        f"Page {r['page']} from {r['source']}: {r['content']}" for r in result["data"]["Get"]["PDFChunk"]
    ]

@app.post("/chat/")
async def chat(request: ChatRequest):
    store_user_message(request.user_id, request.message, "user")
    history = get_user_history(request.user_id)

    retrieved_docs = search_pdf_chunks(request.message, top_k=3)
    context = "\n\n".join(retrieved_docs)

    prompt_messages = history + [
        {"role": "system", "content": "You are a helpful cooking assistant. Use the following document excerpts to answer:\n" + context},
        {"role": "user", "content": request.message}
    ]

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "messages": prompt_messages,
        "stream": False
    })

    data = response.json()
    reply = data["message"]["content"]
    store_user_message(request.user_id, reply, "assistant")

    return {"response": reply}

