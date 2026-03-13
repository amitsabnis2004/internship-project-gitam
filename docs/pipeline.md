**1) PDF chunking: how documents are split and stored**
Implemented in ```context_service.py```, with knobs in ```config.py```.

- Text extraction:
  - Uses pypdf PdfReader page-by-page.
  - Each page is normalized by:
    - null-byte removal
    - bullet character cleanup
    - whitespace collapsing
- Page-aware chunking:
  - Splits each page into word windows, not character windows.
  - Default chunk size = 220 words.
  - Default overlap = 40 words.
  - Step size = chunk_size - overlap = 180 words.
- Low-signal filtering:
  - Drops noisy chunks using heuristics:
    - letter density < 0.35
    - unique_word_ratio < 0.2
  - This is designed for calendar-style PDFs where table-like pages can be very noisy.
- Metadata:
  - Each stored chunk is prefixed with page info like [Page N].
  - SHA-256 hash of full extracted text is used for duplicate detection.
  - replace_existing=true clears old context and rebuilds index.
- Storage:
  - context_documents table: document metadata
  - context_chunks table: chunk text and chunk order
  - Models are in models.py.

**2) PDF retrieval scoring: how relevant chunks are selected**
Also in ```context_service.py```.

For a user query, every chunk gets a hybrid score:

Final score = 0.45 × TF-IDF cosine + 0.40 × semantic cosine + 0.15 × keyword overlap

Where:
- TF-IDF cosine:
  - vectorizer: unigrams + bigrams
  - English stop words removed
  - cosine similarity between query vector and chunk vectors
- Semantic cosine (optional):
  - sentence-transformers all-MiniLM-L6-v2
  - enabled only when CONTEXT_ENABLE_SEMANTIC_RETRIEVAL=true
  - otherwise this term is effectively 0
- Keyword overlap:
  - token overlap ratio between query tokens and chunk tokens

Then:
- Scores are sorted descending.
- Top-k chunks returned (default top_k = 4 from config).

**3) FAQ NLP pipeline (ESRIF style): how base answer/confidence is computed**
Implemented in ```nlp_engine.py```, configured in ```config.py```.

- Preprocessing:
  - lowercase
  - remove non-alphanumeric chars
  - collapse spaces
- Intent classification:
  - Rule-based keyword mapping to:
    - Admissions, Fees, Examinations, Attendance, Placements, Academics, General
- Intent filtering:
  - Candidate FAQs are first restricted to predicted intent.
  - If none found, fallback to all FAQs.
- FAQ scoring:
  - FAQ search text = preprocessed question + intent context terms
  - TF-IDF similarity computed
  - Optional semantic similarity if ENABLE_SEMANTIC_EMBEDDINGS=true
  - Combined similarity = average(TF-IDF, semantic)
  - Final FAQ score:
    - Final = ALPHA × similarity + BETA × keyword_overlap
    - Defaults: ALPHA=0.8, BETA=0.2
- Escalation logic:
  - Threshold defaults to 0.45
  - Soft threshold for non-General intents:
    - max(0.35, threshold - 0.1)

**4) Orchestration: how both pipelines are fused**
Implemented in ```chatbot_service.py```.

Per query:
- Run FAQ pipeline to get:
  - intent, confidence, FAQ fallback answer
- Run PDF retrieval pipeline to get top context chunks
- Send query + chunks to LLM generator in llm_service.py
- If LLM returns valid grounded answer:
  - use that
- Else:
  - use FAQ answer if reliable
  - otherwise formal helpdesk fallback message

**5) Safety NLP layer on final output**
In ```chatbot_service.py``` and ```llm_service.py```.

- Internal markers are blocked and sanitized.
- Technical wording like insufficient context is filtered out.
- Source/debug suffixes are removed for student-facing output.
- Final output is forced into formal helpdesk style when fallback is needed.

If you want, I can also provide this as a short algorithm section you can paste directly into your internship report (with pseudocode blocks).