from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import datetime
import requests

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    message: str

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:1b"  # Your running model

def store_user_message(user_id, message, role):
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO history (user_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, role, message, datetime.datetime.now()),
    )
    conn.commit()
    conn.close()

def get_user_history(user_id):
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute(
        "SELECT role, message FROM history WHERE user_id=? ORDER BY timestamp ASC",
        (user_id,),
    )
    rows = c.fetchall()
    conn.close()
    return [{"role": role, "content": msg} for role, msg in rows]

@app.post("/chat/")
async def chat(request: ChatRequest):
    store_user_message(request.user_id, request.message, "user")
    history = get_user_history(request.user_id)
    # Append current user message again to history for prompt completeness
    history.append({"role": "user", "content": request.message})

    # Send chat request to Ollama API
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": history,
            "stream": False
        },
    )
    data = response.json()
    reply = data["message"]["content"]
    store_user_message(request.user_id, reply, "assistant")

    return {"response": reply}
