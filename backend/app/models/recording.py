import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import TEXT as SQLiteText
from app.core.database import Base

class Recording(Base):
    __tablename__ = "recordings"
    id: Mapped[str] = mapped_column(SQLiteText, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(SQLiteText, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    audio_path: Mapped[str] = mapped_column(String(500), nullable=False)
    audio_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    language: Mapped[str] = mapped_column(String(10), default="zh")
    metadata_json: Mapped[str] = mapped_column(SQLiteText, default="{}")
    summary_json: Mapped[str | None] = mapped_column(SQLiteText, nullable=True)
    qa_json: Mapped[str | None] = mapped_column(SQLiteText, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    transcripts: Mapped[list["Transcript"]] = relationship("Transcript", back_populates="recording", cascade="all, delete-orphan")
    interview_report: Mapped[list["InterviewReport"]] = relationship("InterviewReport", back_populates="recording", cascade="all, delete-orphan")
