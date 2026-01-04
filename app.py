import os
import pandas as pd
import requests
from fastapi import FastAPI, Request

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# -----------------------------
# LOAD FAQ
# -----------------------------
faq = pd.read_csv("ecommerce_faq_final.csv")

faq_data = dict(zip(faq["question"].str.lower(), faq["answer"]))

# -----------------------------
# SIMPLE FAQ LOGIC
# -----------------------------
def faq_chatbot(user_text):
    user_text = user_text.lower()

    for q, a in faq_data.items():
        if q in user_text or user_text in q:
            return a

    return "Sorry, I couldn’t find an answer. Please contact support."

# -----------------------------
# FASTAPI
# -----------------------------
app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text.lower() in ["/start", "start"]:
        reply = (
            "👋 Welcome to Ecommerce FAQ Bot!\n\n"
            "Ask about:\n"
            "- Order tracking\n"
            "- Payments\n"
            "- Returns"
        )
    else:
        reply = faq_chatbot(text)

    send_message(chat_id, reply)
    return {"ok": True}
