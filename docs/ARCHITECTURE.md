# System Architecture

## Overview

The solution uses a modular full-stack design:

- Frontend UI for student and admin interaction
- REST API backend for business logic
- NLP service implementing ESRIF retrieval
- Relational persistence for FAQs, logs, and feedback

## Components

1. `app/main.py`
- Bootstraps FastAPI app
- Serves static assets and templates
- Creates DB schema and seeds FAQ data on startup

2. Routers
- `app/routers/chat.py`: query handling, history, feedback
- `app/routers/admin.py`: FAQ CRUD, unresolved escalations, manual resolve
- `app/routers/analytics.py`: aggregate insights

3. NLP Service
- `app/services/nlp_engine.py`
- Implements:
  - text preprocessing
  - intent prediction
  - intent-based candidate filtering
  - TF-IDF + optional Sentence-BERT similarity
  - keyword overlap
  - weighted hybrid score and escalation threshold

4. Data Layer
- `app/models.py`: FAQ, ConversationLog, Feedback
- `app/db.py`: SQLAlchemy engine and session dependency

## ESRIF Pipeline

1. Receive user query
2. Normalize text
3. Predict intent domain
4. Filter FAQ candidates by intent
5. Compute semantic + lexical similarity
6. Compute final weighted score
7. Return best answer or escalate to admin
8. Persist interaction for analytics and review

## Extensibility

- Swap intent classifier with ML model
- Replace SQLite with PostgreSQL/MySQL
- Add role-based access and SSO
- Add multilingual embeddings and translation
- Add retraining pipeline from feedback data
