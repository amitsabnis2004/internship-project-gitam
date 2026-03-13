import hashlib
import re
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.config import PDF_CHUNK_OVERLAP_WORDS, PDF_CHUNK_SIZE_WORDS
from app.models import ContextChunk, ContextDocument


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_text = _normalize_text(page_text)
        if page_text:
            pages.append(page_text)
    return "\n".join(pages).strip()


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


def ingest_pdf_context(
    db: Session,
    file_name: str,
    file_bytes: bytes,
    replace_existing: bool = False,
) -> dict[str, Any]:
    text = _extract_pdf_text(file_bytes)
    if not text:
        raise ValueError("No extractable text found in this PDF.")

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    existing = (
        db.query(ContextDocument)
        .filter(ContextDocument.content_hash == content_hash)
        .first()
    )
    if existing:
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

    chunks = _chunk_text(text)
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
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(chunk_texts)
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix).flatten()

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
