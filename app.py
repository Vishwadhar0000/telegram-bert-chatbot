import os
import requests
import pandas as pd
from fastapi import FastAPI, Request

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================= LOAD FAQ =================
faq_df = pd.read_csv("ecommerce_faq_final.csv")

faq_data = list(zip(
    faq_df["question"].str.lower(),
    faq_df["answer"]
))

def faq_chatbot(user_text: str) -> str:
    user_text = user_text.lower()
    for q, a in faq_data:
        if q in user_text or user_text in q:
            return a
    return "❓ Sorry, I couldn’t find an answer. Try asking about orders, payments, or returns."

# ================= FASTAPI =================
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}


def send_message(chat_id: int, text: str):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    # -------- NORMAL TEXT MESSAGE --------
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.lower() in ["/start", "start"]:
            reply = (
                "👋 Welcome to Ecommerce FAQ Bot!\n\n"
                "Ask me about:\n"
                "• Order tracking\n"
                "• Payments\n"
                "• Returns"
            )
        else:
            reply = faq_chatbot(text)

        send_message(chat_id, reply)

    # -------- BUTTON / CALLBACK --------
    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        text = data["callback_query"]["data"]

        reply = faq_chatbot(text)
        send_message(chat_id, reply)

    return {"ok": True}

