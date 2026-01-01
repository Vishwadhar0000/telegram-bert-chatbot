from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    reply = f"You said: {text}"

    requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
        json={"chat_id": chat_id, "text": reply}
    )

    return {"ok": True}
