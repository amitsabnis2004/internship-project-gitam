from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    message: str = Field(..., min_length=2)
    user_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    detected_intent: str
    escalated: bool
    conversation_id: int


class FAQBase(BaseModel):
    question: str
    answer: str
    intent: str


class FAQCreate(FAQBase):
    pass


class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    intent: Optional[str] = None
    is_active: Optional[bool] = None


class FAQOut(FAQBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    conversation_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class FeedbackOut(BaseModel):
    id: int
    conversation_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
