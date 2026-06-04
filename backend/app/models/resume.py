import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.sqlite import TEXT as SQLiteText
from app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[str] = mapped_column(SQLiteText, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(SQLiteText, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    parsed_data_json: Mapped[str] = mapped_column(SQLiteText, default="{}")
    raw_text: Mapped[str | None] = mapped_column(SQLiteText, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
