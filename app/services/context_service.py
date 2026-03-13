import hashlib
import re
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.config import (
    CONTEXT_ENABLE_SEMANTIC_RETRIEVAL,
    PDF_CHUNK_OVERLAP_WORDS,
    PDF_CHUNK_SIZE_WORDS,
)
from app.models import ContextChunk, ContextDocument

_SEMANTIC_MODEL: Any | None = None


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = text.replace("\u2022", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_pdf_pages(file_bytes: bytes) -> list[tuple[int, str]]:
    reader = PdfReader(BytesIO(file_bytes))
    pages: list[tuple[int, str]] = []
    for page_index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        page_text = _normalize_text(page_text)
        if page_text:
            pages.append((page_index, page_text))
    return pages


def _is_low_signal_text(text: str) -> bool:
    if not text:
        return True
    chars = len(text)
    letters = len(re.findall(r"[A-Za-z]", text))
    words = text.split()
    unique_words = len(set(words))

    # Typical low-signal calendar grid pages have very low letter density
    # and many repeated numeric/date tokens.
    if chars > 0 and (letters / chars) < 0.35:
        return True
    if len(words) > 0 and (unique_words / len(words)) < 0.2:
        return True
    return False


def _chunk_text(text: str) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunk_size = max(50, PDF_CHUNK_SIZE_WORDS)
    overlap = max(0, min(PDF_CHUNK_OVERLAP_WORDS, chunk_size - 1))
    step = chunk_size - overlap

    chunks: list[str] = []
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            continue
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break

    return chunks


def _get_semantic_model() -> Any | None:
    global _SEMANTIC_MODEL
    if not CONTEXT_ENABLE_SEMANTIC_RETRIEVAL:
        return None

    if _SEMANTIC_MODEL is not None:
        return _SEMANTIC_MODEL

    try:
        from sentence_transformers import SentenceTransformer

        _SEMANTIC_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        _SEMANTIC_MODEL = None
    return _SEMANTIC_MODEL


def _keyword_overlap(query: str, text: str) -> float:
    q_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    t_tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    if not q_tokens:
        return 0.0
    return len(q_tokens.intersection(t_tokens)) / len(q_tokens)


def ingest_pdf_context(
    db: Session,
    file_name: str,
    file_bytes: bytes,
    replace_existing: bool = False,
) -> dict[str, Any]:
    pages = _extract_pdf_pages(file_bytes)
    if not pages:
        raise ValueError("No extractable text found in this PDF.")

    text = "\n".join(page_text for _, page_text in pages).strip()

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    existing = (
        db.query(ContextDocument)
        .filter(ContextDocument.content_hash == content_hash)
        .first()
    )
    if existing and not replace_existing:
        return {
            "file_name": existing.file_name,
            "chunks_added": 0,
            "total_chunks": existing.chunk_count,
            "status": "duplicate",
        }

    if replace_existing:
        db.query(ContextChunk).delete()
        db.query(ContextDocument).delete()
        db.commit()

    chunks: list[str] = []
    for page_number, page_text in pages:
        page_chunks = _chunk_text(page_text)
        for chunk in page_chunks:
            if _is_low_signal_text(chunk):
                continue
            chunks.append(f"[Page {page_number}] {chunk}")

    if not chunks:
        raise ValueError("PDF text is too short or invalid for chunking.")

    document = ContextDocument(
        file_name=file_name,
        content_hash=content_hash,
        chunk_count=len(chunks),
    )
    db.add(document)
    db.flush()

    for i, chunk in enumerate(chunks):
        db.add(
            ContextChunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk,
            )
        )

    db.commit()

    return {
        "file_name": file_name,
        "chunks_added": len(chunks),
        "total_chunks": len(chunks),
        "status": "ok",
    }


def list_context_documents(db: Session) -> list[dict[str, Any]]:
    docs = db.query(ContextDocument).order_by(ContextDocument.created_at.desc()).all()
    return [
        {
            "id": doc.id,
            "file_name": doc.file_name,
            "chunk_count": doc.chunk_count,
            "created_at": doc.created_at,
        }
        for doc in docs
    ]


def retrieve_relevant_chunks(
    db: Session,
    query: str,
    top_k: int,
) -> list[dict[str, Any]]:
    rows = (
        db.query(ContextChunk, ContextDocument)
        .join(ContextDocument, ContextChunk.document_id == ContextDocument.id)
        .all()
    )
    if not rows:
        return []

    chunk_texts = [chunk.content for chunk, _ in rows]

    # Lexical scores for exact phrases and dates.
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(chunk_texts)
    query_vector = vectorizer.transform([query])
    tfidf_scores = cosine_similarity(query_vector, matrix).flatten()

    # Semantic scores improve matches for paraphrased student queries.
    semantic_scores = [0.0 for _ in chunk_texts]
    semantic_model = _get_semantic_model()
    if semantic_model is not None:
        try:
            chunk_embeddings = semantic_model.encode(chunk_texts)
            query_embedding = semantic_model.encode([query])
            semantic_scores = cosine_similarity(query_embedding, chunk_embeddings).flatten().tolist()
        except Exception:
            semantic_scores = [0.0 for _ in chunk_texts]

    keyword_scores = [_keyword_overlap(query, text) for text in chunk_texts]

    scores = []
    for i in range(len(chunk_texts)):
        final = (0.45 * float(tfidf_scores[i])) + (0.4 * float(semantic_scores[i])) + (0.15 * float(keyword_scores[i]))
        scores.append(final)

    ranked = sorted(
        enumerate(scores),
        key=lambda item: item[1],
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    for idx, score in ranked[: max(1, top_k)]:
        chunk, doc = rows[idx]
        selected.append(
            {
                "source": doc.file_name,
                "content": chunk.content,
                "score": round(float(score), 4),
            }
        )

    return selected
