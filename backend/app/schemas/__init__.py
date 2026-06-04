from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# === Auth ===
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: Optional[str] = None
    password: str = Field(..., min_length=6)

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# === Recording ===
class RecordingResponse(BaseModel):
    id: str
    title: str
    audio_duration: Optional[float] = None
    audio_format: Optional[str] = None
    status: str
    language: str
    created_at: datetime

class RecordingDetailResponse(RecordingResponse):
    transcripts: list["TranscriptResponse"] = []

# === Transcript ===
class TranscriptResponse(BaseModel):
    id: str
    speaker: str
    speaker_name: Optional[str] = None
    content: str
    start_time: float
    end_time: float
    confidence: float

# === Resume ===
class ResumeResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    parsed_data: dict = {}
    raw_text: Optional[str] = None
    created_at: datetime

# === Interview ===
class AnalyzeRequest(BaseModel):
    recording_id: str
    resume_id: Optional[str] = None
    job_description: Optional[str] = None

class QAPairResponse(BaseModel):
    id: str
    question: str
    question_category: Optional[str] = None
    your_answer: Optional[str] = None
    best_answer: Optional[str] = None
    answer_score: Optional[float] = None
    improvement_suggestions: Optional[str] = None

class KnowledgePointResponse(BaseModel):
    id: str
    title: str
    category: Optional[str] = None
    key_concepts: list[str] = []
    content: str
    resources: list[dict] = []
    interview_tips: list[str] = []

class InterviewReportResponse(BaseModel):
    id: str
    recording_id: str
    resume_id: Optional[str] = None
    overall_score: Optional[float] = None
    strengths: list[str] = []
    weaknesses: list[str] = []
    improvement_plan: list[dict] = []
    summary: Optional[str] = None
    qa_pairs: list[QAPairResponse] = []
    knowledge_points: list[KnowledgePointResponse] = []
    created_at: datetime

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    estimated_time: Optional[int] = None
