import os
import logging

import requests
import pandas as pd
from fastapi import FastAPI, Request

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)

# ================= LOAD FAQ =================

# CSV must be in the same directory as this app.py on Render
faq_df = pd.read_csv("ecommerce_faq_final.csv")

# Store questions in lowercase for easier matching
faq_data = list(zip(
    faq_df["question"].str.lower(),
    faq_df["answer"]
))

def faq_chatbot(user_text: str) -> str:
    """Simple rule-based matcher over the FAQ CSV."""
    user_text = user_text.lower().strip()

    # 1) Exact question match
    for q, a in faq_data:
        if user_text == q:
            return a

    # 2) Keyword/partial match (any meaningful word in the stored question)
    words = [w for w in user_text.split() if len(w) > 3]
    for q, a in faq_data:
        if any(w in q for w in words):
            return a

    # 3) Fallback
    return "❓ Sorry, I couldn’t find an answer. Try asking about orders, payments, or returns."

# ================= TELEGRAM HELPERS =================

def send_message(chat_id: int, text: str):
    """Send a message with persistent reply keyboard."""
    url = f"{TELEGRAM_API}/sendMessage"

    keyboard = {
        "keyboard": [
            [{"text": "📦 Track Order"}, {"text": "💳 Payments"}],
            [{"text": "↩️ Returns"}, {"text": "🆘 Help"}]
        ],
        "resize_keyboard": True
    }

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard
    }

    r = requests.post(url, json=payload)
    logging.info(f"sendMessage status={r.status_code}, body={r.text}")

# Map button texts to canonical FAQ questions
BUTTON_MAP = {
    "📦 track order": "How can I track my order?",
    "💳 payments": "What payment methods do you accept?",
    "↩️ returns": "What is your return policy?",
    "🆘 help": "How can I contact customer support?"
}

# ================= FASTAPI APP =================

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    logging.info(f"Incoming update: {data}")

    # -------- NORMAL TEXT MESSAGE --------
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        if text.lower() in ["/start", "start"]:
            reply = (
                "👋 Welcome to Ecommerce FAQ Bot!\n\n"
                "Ask me about:\n"
                "• Order tracking\n"
                "• Payments\n"
                "• Returns\n"
                "• Help"
            )
        else:
            key = text.lower()
            if key in BUTTON_MAP:
                # Button pressed → map to known FAQ question
                reply = faq_chatbot(BUTTON_MAP[key])
            else:
                # Free-text question → match against CSV
                reply = faq_chatbot(text)

        send_message(chat_id, reply)

    # (Optional) callbacks can be added here if you later use inline keyboards
    return {"ok": True}
