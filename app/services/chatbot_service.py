import json
import re
from typing import List

from sqlalchemy.orm import Session

from app.config import CONTEXT_TOP_K, FAQ_SEED_PATH
from app.models import ConversationLog, FAQ
from app.services.context_service import retrieve_relevant_chunks
from app.services.llm_service import generate_grounded_answer
from app.services.nlp_engine import ESRIFEngine, FAQDoc

engine = ESRIFEngine()


def _formal_helpdesk_fallback(detected_intent: str) -> str:
    return (
        "Thank you for your query. At the moment, we do not have a verified update for this request "
        "in the current helpdesk knowledge base. Please contact the Student Helpdesk office for the "
        "latest confirmed details. "
        f"(Category: {detected_intent})"
    )


def _sanitize_student_answer(answer: str, detected_intent: str) -> str:
    text = (answer or "").strip()
    if not text:
        return _formal_helpdesk_fallback(detected_intent)

    upper = text.upper()
    blocked_literals = [
        "__INSUFFICIENT_CONTEXT__",
        "__NO_ANSWER__",
        "INSUFFICIENT_CONTEXT",
    ]
    blocked_patterns = [
        r"\binsufficient\s*[_\- ]?\s*context\b",
        r"\bno\s*[_\- ]?\s*answer\b",
    ]

    if any(token in upper for token in blocked_literals):
        return _formal_helpdesk_fallback(detected_intent)

    for pattern in blocked_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return _formal_helpdesk_fallback(detected_intent)

    # Remove internal/retrieval-style wording if it slips through.
    replacements = [
        (r"\bin the context\b", "in the current academic records"),
        (r"\bprovided in the context\b", "currently available in academic records"),
        (r"\bas per the context\b", "as per current academic records"),
        (r"\bfrom the context\b", "from current academic records"),
        (r"\baccording to the context\b", "according to current academic records"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Remove trailing source tags from student-facing answers.
    text = re.sub(r"\s*Sources:\s*\[[^\]]+\](?:\s*,\s*\[[^\]]+\])*\.?\s*$", "", text, flags=re.IGNORECASE)
    text = text.strip()

    return text


def seed_faqs_if_needed(db: Session) -> None:
    if db.query(FAQ).count() > 0:
        return

    if not FAQ_SEED_PATH.exists():
        return

    with FAQ_SEED_PATH.open("r", encoding="utf-8") as fp:
        records = json.load(fp)

    for item in records:
        db.add(
            FAQ(
                question=item["question"],
                answer=item["answer"],
                intent=item["intent"],
                is_active=True,
            )
        )
    db.commit()


def _load_active_faq_docs(db: Session) -> List[FAQDoc]:
    faqs = db.query(FAQ).filter(FAQ.is_active.is_(True)).all()
    return [FAQDoc(id=f.id, question=f.question, answer=f.answer, intent=f.intent) for f in faqs]


def refresh_engine(db: Session) -> None:
    docs = _load_active_faq_docs(db)
    if docs:
        engine.fit(docs)
    else:
        engine.faqs = []


def process_query(db: Session, message: str, user_id: str | None = None) -> ConversationLog:
    result = engine.answer_query(message)

    context_chunks = retrieve_relevant_chunks(db, message, top_k=CONTEXT_TOP_K)
    llm_result = generate_grounded_answer(
        user_query=message,
        context_chunks=context_chunks,
        faq_fallback=result.get("faq_answer", ""),
    )

    if llm_result["used_llm"]:
        answer = _sanitize_student_answer(llm_result["answer"], result["detected_intent"])
        confidence = max(
            float(result["confidence"]),
            max((float(c["score"]) for c in context_chunks), default=0.0),
        )
        escalated = answer == _formal_helpdesk_fallback(result["detected_intent"])
    else:
        faq_answer = (result.get("faq_answer") or "").strip()
        if faq_answer and not bool(result["escalated"]):
            answer = _sanitize_student_answer(faq_answer, result["detected_intent"])
            confidence = float(result["confidence"])
            escalated = answer == _formal_helpdesk_fallback(result["detected_intent"])
        else:
            answer = _formal_helpdesk_fallback(result["detected_intent"])
            confidence = float(result["confidence"])
            escalated = True

    log = ConversationLog(
        user_id=user_id,
        query=message,
        normalized_query=engine.preprocess(message),
        detected_intent=result["detected_intent"],
        response=answer,
        confidence=confidence,
        escalated=escalated,
        resolved_by_admin=False,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
