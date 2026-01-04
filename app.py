import os
import requests
import pandas as pd
from fastapi import FastAPI, Request

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ---------- LOAD FAQ ----------
faq = pd.read_csv("ecommerce_faq_final.csv")

faq_pairs = list(zip(
    faq["question"].str.lower(),
    faq["answer"]
))

def faq_chatbot(text: str):
    text = text.lower()
    for q, a in faq_pairs:
        if q in text or text in q:
            return a
    return "❓ Sorry, I couldn’t find an answer. Please contact support."

# ---------- FASTAPI ----------
app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

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
            "You can ask about:\n"
            "- order tracking\n"
            "- payments\n"
            "- returns"
        )
    else:
        reply = faq_chatbot(text)

    send_message(chat_id, reply)
    return {"ok": True}
