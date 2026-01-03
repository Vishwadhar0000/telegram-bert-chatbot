# ===============================
# 1. IMPORTS
# ===============================
import os
import requests
from fastapi import FastAPI, Request


# ===============================
# 2. CONFIG
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ===============================
# 3. FAQ LOGIC (ALWAYS REPLIES)
# ===============================
def faq_chatbot(user_text: str) -> str:
    text = user_text.lower()

    if "track" in text or "order" in text:
        return "📦 You can track your order by going to *My Orders → Track Order*."

    if "payment" in text or "pay" in text:
        return "💳 We accept Credit Card, Debit Card, UPI, and Net Banking."

    if "return" in text or "refund" in text:
        return "🔁 Returns are accepted within *7 days* of delivery."

    if "help" in text or "support" in text:
        return "🆘 You can contact our support team at support@example.com."

    if text == "/start":
        return (
            "👋 Welcome to the *E-commerce FAQ Bot!*\n\n"
            "You can ask things like:\n"
            "• Track my order\n"
            "• Payment methods\n"
            "• Return policy\n\n"
            "Or use the buttons below 👇"
        )

    # ✅ ALWAYS FALLBACK
    return (
        "❓ I didn’t understand that.\n\n"
        "Please choose one option below or ask:\n"
        "📦 Track Order\n"
        "💳 Payments\n"
        "🔁 Returns\n"
        "🆘 Help"
    )


# ===============================
# 4. FASTAPI APP
# ===============================
app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}


# ===============================
# 5. SEND MESSAGE (WITH BUTTONS)
# ===============================
def send_message(chat_id: int, text: str):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": {
            "keyboard": [
                [{"text": "📦 Track Order"}, {"text": "💳 Payments"}],
                [{"text": "🔁 Returns"}, {"text": "🆘 Help"}],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        },
    }

    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)


# ===============================
# 6. TELEGRAM WEBHOOK
# ===============================
@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"].get("text", "")

    reply = faq_chatbot(user_text)
    send_message(chat_id, reply)

    return {"ok": True}
