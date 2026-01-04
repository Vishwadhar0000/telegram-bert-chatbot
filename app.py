import os
import pandas as pd
import requests
from fastapi import FastAPI, Request
from sentence_transformers import SentenceTransformer, util

# -----------------------------
# CONFIG
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# -----------------------------
# LOAD FAQ + BERT (ONCE)
# -----------------------------
faq_df = pd.read_csv("ecommerce_faq_final.csv")

questions = faq_df["question"].tolist()
answers = faq_df["answer"].tolist()

model = SentenceTransformer("all-MiniLM-L6-v2")
question_embeddings = model.encode(questions, convert_to_tensor=True)

# -----------------------------
# FAQ CHATBOT LOGIC
# -----------------------------
def faq_chatbot(user_text):
    user_embedding = model.encode(user_text, convert_to_tensor=True)
    scores = util.cos_sim(user_embedding, question_embeddings)[0]

    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()

    if best_score < 0.5:
        return "Sorry, I couldn’t find a relevant answer. Please contact support."

    return answers[best_idx]

# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

# -----------------------------
# SEND MESSAGE TO TELEGRAM
# -----------------------------
def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        }
    )

# -----------------------------
# TELEGRAM WEBHOOK
# -----------------------------
@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"].get("text", "")

    if user_text.lower() in ["/start", "start"]:
        reply = (
            "👋 Welcome to Ecommerce FAQ Bot!\n\n"
            "You can ask questions like:\n"
            "- How do I track my order?\n"
            "- What payment methods are available?\n"
            "- What is the return policy?"
        )
    else:
        reply = faq_chatbot(user_text)

    send_message(chat_id, reply)
    return {"ok": True}
