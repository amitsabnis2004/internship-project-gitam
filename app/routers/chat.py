from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ConversationLog, Feedback
from app.schemas import FeedbackCreate, FeedbackOut, QueryRequest, QueryResponse
from app.services.chatbot_service import process_query

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=QueryResponse)
def chat_query(payload: QueryRequest, db: Session = Depends(get_db)):
    log = process_query(db, payload.message, payload.user_id)
    return QueryResponse(
        answer=log.response,
        confidence=log.confidence,
        detected_intent=log.detected_intent,
        escalated=log.escalated,
        conversation_id=log.id,
    )


@router.get("/history")
def chat_history(user_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(ConversationLog).order_by(ConversationLog.created_at.desc())
    if user_id:
        query = query.filter(ConversationLog.user_id == user_id)

    records = query.limit(100).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "query": r.query,
            "answer": r.response,
            "intent": r.detected_intent,
            "confidence": r.confidence,
            "escalated": r.escalated,
            "created_at": r.created_at,
        }
        for r in records
    ]


@router.post("/feedback", response_model=FeedbackOut)
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    conversation = db.get(ConversationLog, payload.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    feedback = Feedback(
        conversation_id=payload.conversation_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
