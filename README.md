
# 💬 BERT-Powered E-Commerce FAQ Conversational Agent

An applied NLP microservice utilizing **BERT semantic embeddings** and an asynchronous **FastAPI** backend to automate customer service query resolution. Rather than relying on static keyword lookups or brittle rule-based matching, this engine maps incoming queries into high-dimensional semantic vector spaces to match against an indexed e-commerce FAQ knowledge base.

---

## 📌 Architecture & Design Highlights
- **Contextual Semantic Matching:** Generates dense contextual representations using pre-trained BERT transformer embeddings to resolve user intent and handle out-of-vocabulary queries.
- **Asynchronous API Engine:** Built with **FastAPI** for high-throughput, low-latency request serving, structured request validation, and webhook dispatching.
- **Client Integration:** Direct webhook integration with the **Telegram Bot API**, supporting continuous multi-turn session contexts and real-time query resolution.
- **Cloud Deployment Architecture:** Configured via Infrastructure-as-Code (`render.yaml`) for automated continuous deployment and zero-downtime hosting on Render.
- **Graceful Fallbacks:** Implements cosine confidence thresholding to automatically trigger structured customer support fallback directives on ambiguous queries.

---

## 🏗️ System Workflow

```text
User Query (Telegram Client)
            │
            ▼
Telegram Webhook Dispatch
            │
            ▼
FastAPI Application Layer (`app.py`)
            │
            ▼
BERT Tokenization & Dense Embedding Extraction
            │
            ▼
Cosine Similarity Search over FAQ Embeddings (`ecommerce_faq_final.csv`)
            │
            ▼
Confidence Threshold Evaluation
    ├── High Confidence Score ──► Return Targeted Answer
    └── Low Confidence Score  ──► Graceful Fallback to Support Directives
