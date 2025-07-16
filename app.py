import streamlit as st
import requests

st.title("🍽️ Recipe & Meal Chatbot")

user_id = "demo_user"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("What do you feel like eating today?", "")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    response = requests.post("http://localhost:8000/chat/", json={"user_id": user_id, "message": user_input})
    bot_reply = response.json()["response"]
    st.session_state.chat_history.append(("bot", bot_reply))

for role, message in st.session_state.chat_history:
    st.write(f"**{role.capitalize()}**: {message}")
