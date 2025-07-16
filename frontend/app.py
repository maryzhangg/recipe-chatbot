import streamlit as st
import requests

API_URL = "http://localhost:8000/chat/"

st.title("PDF Recipe Chatbot with Ollama + Weaviate")

user_id = "user_1"

if "messages" not in st.session_state:
    st.session_state.messages = []

def send_message():
    user_msg = st.session_state.input_text
    st.session_state.messages.append({"role": "user", "content": user_msg})
    st.session_state.input_text = ""

    response = requests.post(API_URL, json={"user_id": user_id, "message": user_msg})
    bot_msg = response.json()["response"]
    st.session_state.messages.append({"role": "assistant", "content": bot_msg})

st.text_input("Ask me anything about your recipes!", key="input_text", on_change=send_message)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Bot:** {msg['content']}")
