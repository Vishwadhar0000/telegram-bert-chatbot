import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": f"You said: {text}"}
    )

    return {"ok": True}
