#imports
import os
import pandas as pd
import torch
import requests
from fastapi import FastAPI, Request
from sentence_transformers import SentenceTransformer, util


#Load Faq + Bert
# Load FAQ dataset
faq_df = pd.read_csv("ecommerce_faq_final.csv")

questions = faq_df["question"].tolist()
answers = faq_df["answer"].tolist()

# Load BERT model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Encode all FAQ questions once
question_embeddings = model.encode(
    questions,
    convert_to_tensor=True
)


#FAQ Logic Fn

def faq_chatbot(user_text):
    user_embedding = model.encode(
        user_text,
        convert_to_tensor=True
    )

    scores = util.cos_sim(
        user_embedding,
        question_embeddings
    )[0]

    best_index = int(torch.argmax(scores))
    best_score = float(scores[best_index])

    if best_score < 0.5:
        return "Sorry, I couldn't find a relevant answer. Please contact support."

    return answers[best_index]

#FastAPI Installation

app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

#telegram WEBHOOK
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"].get("text", "")

    # FORCE BERT FOR EVERY MESSAGE
    reply = faq_chatbot(user_text)

    send_message(chat_id, reply)
    return {"ok": True}

#send message fn

def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        }
    )

