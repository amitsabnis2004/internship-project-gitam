from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    intent = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    query = Column(Text, nullable=False)
    normalized_query = Column(Text, nullable=False)
    detected_intent = Column(String(100), nullable=False, index=True)
    response = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    escalated = Column(Boolean, default=False, index=True)
    resolved_by_admin = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    feedback = relationship("Feedback", back_populates="conversation", cascade="all, delete")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversation_logs.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 (bad) to 5 (great)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ConversationLog", back_populates="feedback")


class ContextDocument(Base):
    __tablename__ = "context_documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    chunk_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    chunks = relationship("ContextChunk", back_populates="document", cascade="all, delete-orphan")


class ContextChunk(Base):
    __tablename__ = "context_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("context_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    document = relationship("ContextDocument", back_populates="chunks")
