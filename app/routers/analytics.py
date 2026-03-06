from sqlalchemy import func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ConversationLog, Feedback

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    total_queries = db.query(func.count(ConversationLog.id)).scalar() or 0
    escalated_queries = (
        db.query(func.count(ConversationLog.id)).filter(ConversationLog.escalated.is_(True)).scalar() or 0
    )
    unresolved = (
        db.query(func.count(ConversationLog.id))
        .filter(ConversationLog.escalated.is_(True), ConversationLog.resolved_by_admin.is_(False))
        .scalar()
        or 0
    )

    top_intents = (
        db.query(ConversationLog.detected_intent, func.count(ConversationLog.id).label("count"))
        .group_by(ConversationLog.detected_intent)
        .order_by(func.count(ConversationLog.id).desc())
        .limit(5)
        .all()
    )

    avg_confidence = db.query(func.avg(ConversationLog.confidence)).scalar()
    avg_rating = db.query(func.avg(Feedback.rating)).scalar()

    return {
        "total_queries": total_queries,
        "escalated_queries": escalated_queries,
        "unresolved_escalations": unresolved,
        "escalation_rate": round((escalated_queries / total_queries), 4) if total_queries else 0.0,
        "average_confidence": round(float(avg_confidence), 4) if avg_confidence is not None else None,
        "average_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
        "top_intents": [{"intent": t[0], "count": t[1]} for t in top_intents],
    }
