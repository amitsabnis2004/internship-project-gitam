# AI Chatbot Web Portal for Student Helpdesk

This project provides a student-helpdesk chatbot with a web UI, admin dashboard, FAQ management, analytics, and LLM-powered responses grounded by uploaded PDF documents such as academic calendars and policy circulars.

## Features

- Student-facing chat portal
- Admin dashboard for FAQ CRUD, unresolved query review, and PDF context upload
- Retrieval-first NLP pipeline (intent + FAQ ranking)
- OpenRouter LLM response generation grounded on uploaded PDF chunks
- Student-safe fallback responses when information is unavailable
- Conversation + feedback logging in SQLite
- Analytics summary API

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite
- Retrieval/NLP: Scikit-learn TF-IDF, optional sentence-transformers
- LLM provider: OpenRouter
- Frontend: HTML/CSS/Vanilla JS

## Project Structure

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
    context_service.py
    llm_service.py
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

## Setup

1. Create and activate your virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional LLM settings
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_SITE_URL=http://localhost:8000
OPENROUTER_APP_NAME=Student Helpdesk Chatbot

# Optional retrieval settings
CONTEXT_TOP_K=4
PDF_CHUNK_SIZE_WORDS=220
PDF_CHUNK_OVERLAP_WORDS=40

# Keep false unless you explicitly want embedding downloads
ENABLE_SEMANTIC_EMBEDDINGS=false
CONTEXT_ENABLE_SEMANTIC_RETRIEVAL=false
```

4. Run the app:

```bash
uvicorn app.main:app --reload
```

5. Open:

- Student portal: http://127.0.0.1:8000/
- Admin portal: http://127.0.0.1:8000/admin-portal
- API docs: http://127.0.0.1:8000/docs

## How Response Generation Works

1. Student asks a question.
2. System runs FAQ retrieval using intent + hybrid lexical similarity.
3. System retrieves top relevant PDF chunks from uploaded context documents.
4. LLM is called through OpenRouter with strict grounding instructions.
5. If no reliable grounded answer is available, chatbot returns a formal helpdesk fallback.
6. Internal/debug markers are sanitized and never shown to students.

## Student-Safe Output Rules

- No internal tokens or technical system language should appear in chat responses.
- If answer is unknown, user receives a formal helpdesk-style response.
- UI supports bold formatting in bot messages (`**text**`), rendered safely in frontend.

## PDF Context Management

Use Admin Dashboard to upload academic calendar or policy PDFs.

- Upload endpoint: `POST /chat/context/upload`
  - multipart field: `file`
  - query param: `replace_existing=true|false`
- List endpoint: `GET /chat/context/files`

Notes:

- `replace_existing=true` clears existing context and re-indexes uploaded PDF.
- Duplicate PDFs are skipped only when `replace_existing=false`.

## Key API Endpoints

- Chat query: `POST /chat/query`
- Chat history: `GET /chat/history`
- Feedback submit: `POST /chat/feedback`
- FAQ list/create/update/delete: `/admin/faqs`
- Unresolved escalations: `GET /admin/unresolved`
- Resolve escalated query: `POST /admin/resolve/{conversation_id}`
- Analytics summary: `GET /analytics/summary`

## Suggested Validation Flow

1. Start server and open student portal.
2. Upload academic calendar PDF from admin portal.
3. Ask date-specific queries and verify grounded responses.
4. Ask unrelated queries and verify formal fallback behavior.
5. Confirm no internal wording (for example, "insufficient context") appears to students.

## Known Practical Considerations

- PDF extraction quality depends on source PDF quality and structure.
- Scanned/image-only PDFs may require OCR for best reliability.
- Optional embedding features may download models on first use if enabled.

## Future Enhancements

- OCR pipeline for scanned PDF reliability
- Page-level citations in student-facing responses
- Better date normalization and conflict detection
- Authentication and role-based access
- ERP integration and multilingual support
