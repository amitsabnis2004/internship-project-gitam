# AI Chatbot Web Portal for Student Helpdesk (NLP)

This project implements an AI-powered student helpdesk chatbot described in your internship brief. It includes:

- Student chatbot web portal
- NLP pipeline with ESRIF-style retrieval
- Intent filtering and hybrid scoring
- Confidence-based escalation to admin
- Admin dashboard for FAQ management and unresolved queries
- Analytics summary API

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

## 4. Core Features Implemented

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

## 7. Future Enhancements

- Replace rule-based intent classifier with supervised model
- Add multilingual support
- Add authentication/role management
- Integrate ERP APIs
- Add response feedback loop for adaptive retraining
