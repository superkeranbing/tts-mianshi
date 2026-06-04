import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import TEXT as SQLiteText
from app.core.database import Base

class Transcript(Base):
    __tablename__ = "transcripts"
    id: Mapped[str] = mapped_column(SQLiteText, primary_key=True, default=lambda: str(uuid.uuid4()))
    recording_id: Mapped[str] = mapped_column(SQLiteText, ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False)
    speaker: Mapped[str] = mapped_column(String(50), nullable=False)
    speaker_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(SQLiteText, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, default=0.0)
    end_time: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    recording: Mapped["Recording"] = relationship("Recording", back_populates="transcripts")
