# System Architecture

## Overview

The application uses a layered modular design:

- Presentation layer: student and admin web interfaces
- API layer: FastAPI routers for chat, admin, and analytics
- Retrieval layer: FAQ intent/ranking + PDF chunk retrieval
- Generation layer: OpenRouter LLM with grounding constraints
- Safety layer: fallback and output sanitization for student-safe responses
- Persistence layer: SQLite via SQLAlchemy

## Runtime Components

1. App bootstrap

- `app/main.py`
- Responsibilities:
  - FastAPI initialization
  - static/template serving
  - database table creation at startup
  - FAQ seed + retrieval engine refresh

2. Routers

- `app/routers/chat.py`
  - `POST /chat/query`
  - `GET /chat/history`
  - `POST /chat/feedback`
  - `POST /chat/context/upload`
  - `GET /chat/context/files`
- `app/routers/admin.py`
  - FAQ CRUD
  - unresolved escalations and manual resolution
- `app/routers/analytics.py`
  - aggregate usage and escalation metrics

3. Retrieval and generation services

- `app/services/nlp_engine.py`
  - query normalization
  - rule-based intent classification
  - FAQ candidate filtering by intent
  - hybrid lexical scoring
- `app/services/context_service.py`
  - PDF text extraction
  - page-aware chunking
  - low-signal chunk filtering
  - top-k chunk retrieval for a query
- `app/services/llm_service.py`
  - OpenRouter chat completion call
  - grounded prompt construction
  - no-answer signaling
- `app/services/chatbot_service.py`
  - orchestrates FAQ retrieval + PDF retrieval + LLM call
  - applies formal fallback logic
  - sanitizes final student-facing text
  - persists conversation logs

4. Data models

- `app/models.py`
  - `FAQ`
  - `ConversationLog`
  - `Feedback`
  - `ContextDocument`
  - `ContextChunk`
- `app/db.py`
  - SQLAlchemy engine/session wiring

## End-to-End Query Flow

1. Student sends query to `POST /chat/query`.
2. FAQ retrieval computes best candidate + confidence.
3. PDF chunk retriever selects top relevant context blocks.
4. LLM generates grounded answer if possible.
5. If no reliable grounded answer exists:
  - return FAQ answer when confidence is acceptable, else
  - return formal helpdesk fallback.
6. Safety sanitizer strips technical/internal wording before response is returned.
7. Interaction is stored for analytics and admin workflows.

## Safety and Reliability Controls

- Internal token suppression:
  - internal markers are intercepted and never shown to users.
- Student-safe phrasing:
  - avoids technical platform wording in responses.
- Formal fallback:
  - unknown/insufficient info returns a professional helpdesk response.
- Context replacement support:
  - `replace_existing=true` fully refreshes PDF index.

## Data Lifecycle

1. Admin uploads PDF context.
2. PDF text is extracted and chunked.
3. Chunks are stored in `context_documents` and `context_chunks` tables.
4. Query-time retrieval selects relevant chunks.
5. Logs and feedback accumulate for analytics and tuning.

## Scalability and Extension Points

- Swap SQLite with PostgreSQL/MySQL for multi-user deployment.
- Add OCR preprocessing for scanned PDFs.
- Add page-level citations and structured date extraction.
- Replace rule-based intent logic with trained classifier.
- Add authentication, authorization, and audit trails.
