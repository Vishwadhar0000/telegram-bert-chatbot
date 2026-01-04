import os
import pandas as pd
import requests
from fastapi import FastAPI, Request
from sentence_transformers import SentenceTransformer, util

# =============================
# CONFIG
# =============================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =============================
# LOAD MODEL + FAQ
# =============================
model = SentenceTransformer("all-MiniLM-L6-v2")

faq_df = pd.read_csv("ecommerce_faq_final.csv")
questions = faq_df["question"].tolist()
answers = faq_df["answer"].tolist()
question_embeddings = model.encode(questions, convert_to_tensor=True)

# =============================
# FASTAPI APP
# =============================
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

# =============================
# FAQ CHATBOT LOGIC
# =============================
def faq_chatbot(user_query: str) -> str:
    query_embedding = model.encode(user_query, convert_to_tensor=True)
    similarity = util.cos_sim(query_embedding, question_embeddings)
    best_idx = similarity.argmax().item()
    best_score = similarity[0][best_idx].item()

    if best_score > 0.6:
        return answers[best_idx]
    else:
        return "Sorry, I couldn’t find an answer to that. Please try asking differently."

# =============================
# SEND MESSAGE TO TELEGRAM
# =============================
def send_message(chat_id: int, text: str):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(TELEGRAM_API, json=payload)

# =============================
# TELEGRAM WEBHOOK
# =============================
@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"].get("text", "")

    if user_text.startswith("/start"):
        send_message(chat_id, "👋 Welcome! Ask me anything about orders, payments, or returns.")
        return {"ok": True}

    reply = faq_chatbot(user_text)
    send_message(chat_id, reply)

    return {"ok": True}
