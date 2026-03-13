import json
from typing import List

from sqlalchemy.orm import Session

from app.config import CONTEXT_TOP_K, FAQ_SEED_PATH
from app.models import ConversationLog, FAQ
from app.services.context_service import retrieve_relevant_chunks
from app.services.llm_service import generate_grounded_answer
from app.services.nlp_engine import ESRIFEngine, FAQDoc

engine = ESRIFEngine()


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
        answer = llm_result["answer"]
        confidence = max(
            float(result["confidence"]),
            max((float(c["score"]) for c in context_chunks), default=0.0),
        )
        escalated = False
    else:
        answer = result["answer"]
        confidence = float(result["confidence"])
        escalated = bool(result["escalated"])

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
