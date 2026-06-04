import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import TEXT as SQLiteText
from app.core.database import Base

class InterviewReport(Base):
    __tablename__ = "interview_reports"
    id: Mapped[str] = mapped_column(SQLiteText, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(SQLiteText, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recording_id: Mapped[str] = mapped_column(SQLiteText, ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False)
    resume_id: Mapped[str | None] = mapped_column(SQLiteText, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    strengths_json: Mapped[str] = mapped_column(SQLiteText, default="[]")
    weaknesses_json: Mapped[str] = mapped_column(SQLiteText, default="[]")
    improvement_plan_json: Mapped[str] = mapped_column(SQLiteText, default="[]")
    summary: Mapped[str | None] = mapped_column(SQLiteText, nullable=True)
    report_data_json: Mapped[str] = mapped_column(SQLiteText, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    recording: Mapped["Recording"] = relationship("Recording", back_populates="interview_report")
    qa_pairs: Mapped[list["QAPair"]] = relationship("QAPair", back_populates="report", cascade="all, delete-orphan")
    knowledge_points: Mapped[list["KnowledgePoint"]] = relationship("KnowledgePoint", back_populates="report", cascade="all, delete-orphan")

class QAPair(Base):
    __tablename__ = "qa_pairs"
    id: Mapped[str] = mapped_column(SQLiteText, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str] = mapped_column(SQLiteText, ForeignKey("interview_reports.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[str] = mapped_column(SQLiteText, nullable=False)
    question_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    your_answer: Mapped[str | None] = mapped_column(SQLiteText, nullable=True)
    best_answer: Mapped[str | None] = mapped_column(SQLiteText, nullable=True)
    answer_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    improvement_suggestions: Mapped[str | None] = mapped_column(SQLiteText, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    report: Mapped["InterviewReport"] = relationship("InterviewReport", back_populates="qa_pairs")

class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"
    id: Mapped[str] = mapped_column(SQLiteText, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str] = mapped_column(SQLiteText, ForeignKey("interview_reports.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    key_concepts_json: Mapped[str] = mapped_column(SQLiteText, default="[]")
    content: Mapped[str] = mapped_column(SQLiteText, nullable=False)
    resources_json: Mapped[str] = mapped_column(SQLiteText, default="[]")
    interview_tips_json: Mapped[str] = mapped_column(SQLiteText, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    report: Mapped["InterviewReport"] = relationship("InterviewReport", back_populates="knowledge_points")
