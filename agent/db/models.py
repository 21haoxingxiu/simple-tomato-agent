from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    default_workspace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    workspaces: Mapped[list["Workspace"]] = relationship(
        "Workspace", back_populates="owner", cascade="all, delete-orphan"
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["User"] = relationship("User", back_populates="workspaces")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    doc_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="ready")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="knowledge_base", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    kb_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="ready")
    error_msg: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase", back_populates="documents"
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kb_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    seq: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    vector_id: Mapped[str] = mapped_column(String(100), default="")
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), default="新会话")
    kb_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class EvalDataset(Base):
    __tablename__ = "eval_datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cases: Mapped[list["EvalCase"]] = relationship(
        "EvalCase", back_populates="dataset", cascade="all, delete-orphan"
    )


class EvalCase(Base):
    __tablename__ = "eval_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("eval_datasets.id", ondelete="SET NULL"),
        nullable=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dataset: Mapped[Optional["EvalDataset"]] = relationship("EvalDataset", back_populates="cases")
    runs: Mapped[list["EvalRun"]] = relationship(
        "EvalRun", back_populates="case", cascade="all, delete-orphan"
    )


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("eval_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id: Mapped[str] = mapped_column(String(36), default="", index=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    kb_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    actual_answer: Mapped[str] = mapped_column(Text, default="")
    similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    faithfulness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relevance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    error_msg: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped["EvalCase"] = relationship("EvalCase", back_populates="runs")
