# =========================
# 1. IMPORTS
# =========================
import os
import pandas as pd
import numpy as np
import requests

from fastapi import FastAPI, Request
from sentence_transformers import SentenceTransformer, util


# =========================
# 2. CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # set in Render → Environment Variables
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

FAQ_FILE = "ecommerce_faq_final.csv"
SIMILARITY_THRESHOLD = 0.6


# =========================
# 3. LOAD FAQ + MODEL
# =========================
faq_df = pd.read_csv(FAQ_FILE)

questions = faq_df["question"].astype(str).tolist()
answers = faq_df["answer"].astype(str).tolist()

# ✅ PRODUCTION-SAFE MODEL (works on Render Free)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

question_embeddings = model.encode(
    questions, convert_to_tensor=True, show_progress_bar=False
)


# =========================
# 4. FAQ CHATBOT LOGIC
# =========================
def faq_chatbot(user_text: str) -> str:
    user_embedding = model.encode(
        user_text, convert_to_tensor=True, show_progress_bar=False
    )

    scores = util.cos_sim(user_embedding, question_embeddings)[0]
    best_score = float(torch_max(scores))
    best_idx = int(np.argmax(scores.cpu().numpy()))

    if best_score >= SIMILARITY_THRESHOLD:
        return answers[best_idx]

    return (
        "🤖 Sorry, I couldn’t find an exact answer.\n\n"
        "You can try:\n"
        "• Track Order\n"
        "• Payments\n"
        "• Returns\n"
        "• Help"
    )


def torch_max(tensor):
    return tensor.max().item()


# =========================
# 5. FASTAPI APP
# =========================
app = FastAPI()


@app.get("/")
def health_check():
    return {"status": "ok"}


# =========================
# 6. SEND MESSAGE (WITH BUTTONS)
# =========================
def send_message(chat_id: int, text: str):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "keyboard": [
                [{"text": "📦 Track Order"}, {"text": "💳 Payments"}],
                [{"text": "↩️ Returns"}, {"text": "🆘 Help"}],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        },
    }

    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)


# =========================
# 7. TELEGRAM WEBHOOK
# =========================
@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # START COMMAND
    if text.lower() == "/start":
        send_message(
            chat_id,
            "👋 Welcome to the Ecommerce FAQ Bot!\n\n"
            "Use the buttons below or type your question.",
        )
        return {"ok": True}

    # BUTTON NORMALIZATION
    button_map = {
        "📦 Track Order": "How can I track my order?",
        "💳 Payments": "What payment methods are accepted?",
        "↩️ Returns": "What is your return policy?",
        "🆘 Help": "How can I contact support?",
    }

    normalized_text = button_map.get(text, text)

    reply = faq_chatbot(normalized_text)
    send_message(chat_id, reply)

    return {"ok": True}
