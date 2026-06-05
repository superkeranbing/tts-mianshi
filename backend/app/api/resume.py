from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid, os, json
from app.core.database import get_db
from app.core.storage import storage
from app.core.security import require_user
from app.models.resume import Resume
from app.schemas import ResumeResponse
from app.services.resume_parser import resume_parser

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db), user: dict = Depends(require_user)):
    ext = os.path.splitext(file.filename or "resume.pdf")[1]
    safe = f"{uuid.uuid4()}{ext}"
    content = await file.read()
    path = await storage.save_resume(content, safe)
    file_type = ext.lstrip(".")
    parsed = await resume_parser.parse(path, file_type)
    raw_text = parsed.pop("raw_text", "") or await resume_parser._parse_fallback(path)
    resume = Resume(
        user_id=user["id"], file_path=path, file_name=file.filename or "resume",
        file_type=file_type,
        parsed_data_json=json.dumps(parsed, ensure_ascii=False),
        raw_text=raw_text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return ResumeResponse(
        id=resume.id, file_name=resume.file_name, file_type=resume.file_type,
        parsed_data=parsed, raw_text=resume.raw_text, created_at=resume.created_at,
    )

@router.get("", response_model=list[ResumeResponse])
async def list_resumes(db: Session = Depends(get_db), user: dict = Depends(require_user)):
    resumes = db.execute(
        select(Resume).where(Resume.user_id == user["id"]).order_by(Resume.created_at.desc())
    ).scalars().all()
    return [ResumeResponse(
        id=r.id, file_name=r.file_name, file_type=r.file_type,
        parsed_data=json.loads(r.parsed_data_json) if r.parsed_data_json else {},
        raw_text=r.raw_text, created_at=r.created_at,
    ) for r in resumes]

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    r = db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user["id"])
    ).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "简历不存在")
    return ResumeResponse(
        id=r.id, file_name=r.file_name, file_type=r.file_type,
        parsed_data=json.loads(r.parsed_data_json) if r.parsed_data_json else {},
        raw_text=r.raw_text, created_at=r.created_at,
    )