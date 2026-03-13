# AI Chatbot Web Portal for Student Helpdesk (NLP)

This project implements an AI-powered student helpdesk chatbot described in your internship brief. It includes:

- Student chatbot web portal
- NLP pipeline with ESRIF-style retrieval
- Intent filtering and hybrid scoring
- Confidence-based escalation to admin
- Admin dashboard for FAQ management and unresolved queries
- Analytics summary API
- LLM answer generation through OpenRouter
- PDF context upload and retrieval grounding for academic calendar and policy documents

## 1. Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite
- NLP: Scikit-learn TF-IDF + optional Sentence-Transformers embeddings
- Frontend: HTML/CSS/Vanilla JS (served by FastAPI)

## 2. Project Structure

```text
app/
  main.py
  config.py
  db.py
  models.py
  schemas.py
  routers/
    chat.py
    admin.py
    analytics.py
  services/
    nlp_engine.py
    chatbot_service.py
  templates/
    index.html
    admin.html
  static/
    css/styles.css
    js/chat.js
    js/admin.js
data/
  faqs_seed.json
docs/
  ARCHITECTURE.md
```

## 3. Setup

1. Create/activate virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
uvicorn app.main:app --reload
```

4. Open:

- Student portal: `http://127.0.0.1:8000/`
- Admin portal: `http://127.0.0.1:8000/admin-portal`
- API docs: `http://127.0.0.1:8000/docs`

## 4. OpenRouter LLM + PDF Context

Set your OpenRouter API key in `.env` (or OS env vars):

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
# Optional
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_SITE_URL=http://localhost:8000
OPENROUTER_APP_NAME=Student Helpdesk Chatbot
```

How it works now:

1. Upload an academic calendar PDF (or any policy PDF) from Admin Dashboard -> "Upload PDF Context".
2. The system extracts text, chunks it, stores it in DB, and retrieves relevant chunks per query.
3. Chat answers are generated with OpenRouter using only retrieved PDF context.
4. If LLM cannot ground an answer in uploaded context, the system falls back to the existing FAQ retrieval/escalation pipeline.

API endpoints added:

- `POST /chat/context/upload` (multipart file upload, optional `replace_existing=true`)
- `GET /chat/context/files`

## 5. Core Features Implemented

- Query preprocessing: lowercasing, cleanup, normalization
- Intent classification (domain-based rules)
- Intent-based FAQ candidate filtering
- Hybrid score:

```text
Score = alpha * similarity + beta * keyword_overlap
```

Default weights: `alpha=0.8`, `beta=0.2`

- Confidence threshold and escalation (`threshold=0.65`)
- Logging conversation with score and escalation status
- Admin FAQ CRUD APIs
- Analytics summary APIs (counts, escalation rate, top intents)

## 5. Notes on Sentence Embeddings

- `sentence-transformers` is included in dependencies.
- By default, semantic embeddings are disabled to keep startup fast and avoid mandatory model downloads.
- Enable them with:

```bash
set ENABLE_SEMANTIC_EMBEDDINGS=true
uvicorn app.main:app --reload
```

- If model loading fails in a constrained environment, the system falls back to TF-IDF similarity and remains functional.

## 6. Suggested Demo Flow

1. Ask an exam question from student portal.
2. Verify intent and confidence shown under chat input.
3. Ask a vague question; observe escalation behavior.
4. Open admin portal, add a new FAQ, and test the same question again.
5. Upload your academic calendar PDF and ask date/policy queries to validate LLM grounding.

## 7. Future Enhancements

- Replace rule-based intent classifier with supervised model
- Add multilingual support
- Add authentication/role management
- Integrate ERP APIs
- Add response feedback loop for adaptive retraining
