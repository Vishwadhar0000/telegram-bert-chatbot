from fastapi import FastAPI, Request
import requests
import os
from sentence_transformers import SentenceTransformer, util

app = FastAPI()

# Load BERT model once
model = SentenceTransformer("all-MiniLM-L6-v2")

# Get token from Render environment
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"].get("text", "")

    reply = f"You said: {user_text}"

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": reply}
    )

    return {"ok": True}
