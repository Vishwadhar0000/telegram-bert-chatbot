import os
import pandas as pd
import requests

from fastapi import FastAPI, Request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =====================
# CONFIG
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
FAQ_FILE = "ecommerce_faq_final.csv"
SIM_THRESHOLD = 0.3


# =====================
# LOAD FAQ
# =====================
faq_df = pd.read_csv(FAQ_FILE)

questions = faq_df["question"].astype(str).tolist()
answers = faq_df["answer"].astype(str).tolist()

vectorizer = TfidfVectorizer(stop_words="english")
question_vectors = vectorizer.fit_transform(questions)


# =====================
# FAQ LOGIC
# =====================
def faq_chatbot(user_text: str) -> str:
    user_vec = vectorizer.transform([user_text])
    scores = cosine_similarity(user_vec, question_vectors)[0]

    best_idx = scores.argmax()
    best_score = scores[best_idx]

    if best_score >= SIM_THRESHOLD:
        return answers[best_idx]

    return (
        "🤖 Sorry, I couldn’t find an exact answer.\n\n"
        "Try:\n• Track Order\n• Payments\n• Returns\n• Help"
    )


# =====================
# FASTAPI
# =====================
app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}


# =====================
# SEND MESSAGE
# =====================
def send_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "keyboard": [
                [{"text": "📦 Track Order"}, {"text": "💳 Payments"}],
                [{"text": "↩️ Returns"}, {"text": "🆘 Help"}],
            ],
            "resize_keyboard": True,
        },
    }
    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)


# =====================
# TELEGRAM WEBHOOK
# =====================
@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text.lower() == "/start":
        send_message(
            chat_id,
            "👋 Welcome to the Ecommerce FAQ Bot!\n\n"
            "Use the buttons below or ask a question."
        )
        return {"ok": True}

    button_map = {
        "📦 Track Order": "How can I track my order?",
        "💳 Payments": "What payment methods are accepted?",
        "↩️ Returns": "What is your return policy?",
        "🆘 Help": "How can I contact support?",
    }

    normalized = button_map.get(text, text)
    reply = faq_chatbot(normalized)
    send_message(chat_id, reply)

    return {"ok": True}
