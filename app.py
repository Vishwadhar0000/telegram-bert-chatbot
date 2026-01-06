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

# ================= CONVERSATION MEMORY =================

# chat_id -> list of last messages (strings)
conversation_history = {}

# How many previous user messages to keep per chat
MAX_HISTORY = 5

def update_history(chat_id: int, user_text: str):
    history = conversation_history.get(chat_id, [])
    history.append(user_text)
    conversation_history[chat_id] = history[-MAX_HISTORY:]

def build_context(chat_id: int, user_text: str) -> str:
    """
    Build a contextual query from previous messages + current one.
    This runs for all non-/start messages.
    """
    history = conversation_history.get(chat_id, [])
    if not history:
        return user_text
    combined = " ".join(history + [user_text])
    logging.info(f"Context for {chat_id}: {combined}")
    return combined

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

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        if text.lower() in ["/start", "start"]:
            # reset history on /start
            conversation_history[chat_id] = []
            reply = (
                "👋 Welcome to Ecommerce FAQ Bot!\n\n"
                "Ask me about:\n"
                "• Order tracking\n"
                "• Payments\n"
                "• Returns\n"
                "• Help"
            )
        else:
            # update memory for ALL questions
            update_history(chat_id, text)

            key = text.lower()
            if key in BUTTON_MAP:
                # buttons → mapped FAQ question (no extra context needed)
                contextual_query = BUTTON_MAP[key]
            else:
                # any free-text question uses conversation context
                contextual_query = build_context(chat_id, text)

            reply = faq_chatbot(contextual_query)

        send_message(chat_id, reply)

    return {"ok": True}


