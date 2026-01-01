!pip install fastapi uvicorn pandas scikit-learn sentence-transformers pyngrok nest-asyncio requests









import pandas as pd
import numpy as np
import requests
import nest_asyncio
import asyncio

from fastapi import FastAPI, Request
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
import torch











# Load FAQ dataset
df = pd.read_csv("/content/ecommerce_faq_final.csv")

# Keep only required columns
df = df[["question", "answer"]]

# Clean data
df.dropna(inplace=True)
df.reset_index(drop=True, inplace=True)

# Preview dataset
df.head()









# Load Sentence Transformer model
bert_model = SentenceTransformer("all-mpnet-base-v2")









# Convert FAQ questions to embeddings
faq_questions = df["question"].tolist()
faq_answers = df["answer"].tolist()

faq_embeddings = bert_model.encode(
    faq_questions,
    convert_to_tensor=True,
    normalize_embeddings=True
)









CONFIDENCE_THRESHOLD = 0.65

def faq_chatbot(user_input: str, chat_id: int = None) -> str:
    # Add to memory and build context
    if chat_id is not None:
        add_to_memory(chat_id, user_input)
        context = get_context(chat_id)
        combined_input = context + " " + user_input
    else:
        combined_input = user_input

    user_embedding = bert_model.encode(
        combined_input,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    similarity_scores = util.cos_sim(
        user_embedding,
        faq_embeddings
    )

    best_score, best_idx = torch.max(similarity_scores, dim=1)

    if best_score.item() < CONFIDENCE_THRESHOLD:
        return (
            "🤔 I'm not fully sure about that.\n"
            "Could you please give a bit more detail?"
        )

    return faq_answers[best_idx.item()]









print(faq_chatbot("Where can I check my order status?"))
print(faq_chatbot("What payment methods do you support?"))
print(faq_chatbot("How do I return a product?"))








def handle_small_talk(msg: str):
    msg = msg.lower().strip()

    if msg in ["hi", "hello", "hey"]:
        return "Hello 👋 How can I help you today?"

    if "thank" in msg:
        return "You're welcome 😊 Happy to help!"

    if msg in ["bye", "goodbye", "exit"]:
        return "Goodbye 👋 Have a great day!"

    return None









# Create FastAPI app
app = FastAPI(title="E-Commerce FAQ Chatbot API")

# Request body model for /chat endpoint
class ChatRequest(BaseModel):
    message: str








@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message

    # Small talk first
    small_talk = handle_small_talk(user_message)
    if small_talk:
        return {"reply": small_talk}

    # FAQ chatbot (BERT)
    reply = faq_chatbot(user_message)
    return {"reply": reply}








TELEGRAM_BOT_TOKEN = "8597939946:AAEYX1PRkDEhdyiWGdCWGu2-jKChZmJiHus"









@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    # Safety check
    if "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    user_text = data["message"].get("text", "").strip()

    # /start command
    if user_text == "/start":
        send_telegram_message(
            chat_id,
            "👋 Welcome to the E-Commerce FAQ Bot!\n\nPlease choose an option below 👇",
            reply_markup=main_menu_keyboard()
        )
        return {"ok": True}

    # Button handling
    elif user_text == "📦 Track Order":
        reply = faq_chatbot("How can I track my order?", chat_id)

    elif user_text == "💳 Payments":
        reply = faq_chatbot("What payment methods do you accept?", chat_id)

    elif user_text == "↩️ Returns":
        reply = faq_chatbot("What is your return policy?", chat_id)

    elif user_text == "🆘 Help":
        reply = "🆘 Help\n\nUse the buttons or type your question."

    # Normal text / small talk
    else:
        small_talk = handle_small_talk(user_text)
        reply = small_talk if small_talk else faq_chatbot(user_text, chat_id)

    send_telegram_message(chat_id, reply)
    return {"ok": True}








import nest_asyncio
import asyncio
import uvicorn

nest_asyncio.apply()

config = uvicorn.Config(
    app,
    host="0.0.0.0",
    port=8000,
    log_level="info"
)

server = uvicorn.Server(config)
asyncio.get_event_loop().create_task(server.serve())








from pyngrok import ngrok

ngrok.set_auth_token("37UkDjz58mC7GKWbrYOkVi7P0HR_2rk4q6yFKN9huf6yPNStw")







from pyngrok import ngrok

ngrok.kill()
tunnel = ngrok.connect(8000)
public_url = tunnel.public_url

print("Public URL:", public_url)








TELEGRAM_BOT_TOKEN = "8597939946:AAEYX1PRkDEhdyiWGdCWGu2-jKChZmJiHus"







import requests

webhook_url = f"{public_url}/telegram"

requests.get(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
)

response = requests.get(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
    params={"url": webhook_url}
)

print(response.json())










import requests

webhook_url = f"{public_url}/telegram"
print("Setting webhook to:", webhook_url)

# Delete old webhook (safe)
requests.get(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
)

# Set new webhook
response = requests.get(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
    params={"url": webhook_url}
)

print(response.json())







print(type(bert_model))








import inspect
print(inspect.getsource(faq_chatbot))









# Conversation memory (per Telegram user)
conversation_memory = {}

MAX_MEMORY = 5  # number of recent messages to remember











def add_to_memory(chat_id: int, message: str):
    if chat_id not in conversation_memory:
        conversation_memory[chat_id] = []

    conversation_memory[chat_id].append(message)

    # Keep only last N messages
    if len(conversation_memory[chat_id]) > MAX_MEMORY:
        conversation_memory[chat_id].pop(0)


def get_context(chat_id: int) -> str:
    if chat_id not in conversation_memory:
        return ""
    return " ".join(conversation_memory[chat_id])












def main_menu_keyboard():
    return {
        "keyboard": [
            [{"text": "📦 Track Order"}, {"text": "💳 Payments"}],
            [{"text": "↩️ Returns"}, {"text": "🆘 Help"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }










def send_telegram_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json=payload
    )













