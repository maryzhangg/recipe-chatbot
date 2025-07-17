from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import datetime
import requests
import weaviate
from weaviate.classes.config import Configure

# Init DB
def init_db():
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:1b"

# Connect to Weaviate with skip_init_checks=True
client = weaviate.connect_to_local(skip_init_checks=True)

# Get or create collection for PDF chunks
try:
    pdf_chunk_collection = client.collections.get("PDFChunk")
except Exception:
    pdf_chunk_collection = client.collections.create(
        name="PDFChunk",
        vector_config=Configure.Vectors.text2vec_ollama()
    )

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
    results = pdf_chunk_collection.query.near_text(query=query, limit=top_k)
    return [
        f"Page {obj.properties.get('page')} from {obj.properties.get('source')}: {obj.properties.get('content')}"
        for obj in results.objects
    ]

@app.post("/chat/")
async def chat(request: ChatRequest):
    store_user_message(request.user_id, request.message, "user")
    history = get_user_history(request.user_id)

    retrieved_docs = search_pdf_chunks(request.message, top_k=3)
    context = "\n\n".join(retrieved_docs) if retrieved_docs else ""

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
