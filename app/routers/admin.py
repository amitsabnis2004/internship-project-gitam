from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ConversationLog, FAQ
from app.schemas import FAQCreate, FAQOut, FAQUpdate
from app.services.chatbot_service import refresh_engine

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/faqs", response_model=list[FAQOut])
def list_faqs(db: Session = Depends(get_db)):
    return db.query(FAQ).order_by(FAQ.intent.asc(), FAQ.id.asc()).all()


@router.post("/faqs", response_model=FAQOut)
def create_faq(payload: FAQCreate, db: Session = Depends(get_db)):
    faq = FAQ(**payload.model_dump(), is_active=True)
    db.add(faq)
    db.commit()
    db.refresh(faq)
    refresh_engine(db)
    return faq


@router.put("/faqs/{faq_id}", response_model=FAQOut)
def update_faq(faq_id: int, payload: FAQUpdate, db: Session = Depends(get_db)):
    faq = db.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(faq, key, value)

    db.commit()
    db.refresh(faq)
    refresh_engine(db)
    return faq


@router.delete("/faqs/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = db.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    db.delete(faq)
    db.commit()
    refresh_engine(db)
    return {"deleted": True}


@router.get("/unresolved")
def unresolved_queries(db: Session = Depends(get_db)):
    rows = (
        db.query(ConversationLog)
        .filter(ConversationLog.escalated.is_(True), ConversationLog.resolved_by_admin.is_(False))
        .order_by(ConversationLog.created_at.desc())
        .limit(100)
        .all()
    )
    return rows


@router.post("/resolve/{conversation_id}")
def resolve_query(conversation_id: int, admin_response: str, db: Session = Depends(get_db)):
    row = db.get(ConversationLog, conversation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")

    row.response = admin_response
    row.resolved_by_admin = True
    db.commit()
    return {"resolved": True}
