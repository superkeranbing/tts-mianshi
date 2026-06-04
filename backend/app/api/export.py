from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
import io
from app.core.database import get_db
from app.models.recording import Recording
from app.models.transcript import Transcript

router = APIRouter(prefix="/api/export", tags=["Export"])

def _srt(sec): return f"{int(sec//3600):02d}:{int(sec%3600//60):02d}:{int(sec%60):02d},{int(sec%1*1000):03d}"

@router.get("/{recording_id}/txt")
async def export_txt(recording_id: str, db: Session = Depends(get_db)):
    recording = db.execute(select(Recording).where(Recording.id==recording_id)).scalar_one_or_none()
    if not recording: raise HTTPException(404,"录音不存在")
    tl = db.execute(select(Transcript).where(Transcript.recording_id==recording_id).order_by(Transcript.start_time)).scalars().all()
    lines = [f"标题: {recording.title}\n"]
    for t in tl:
        sp = t.speaker_name or t.speaker; ts = f"[{int(t.start_time//60):02d}:{int(t.start_time%60):02d}]"
        lines.append(f"{ts} {sp}: {t.content}\n")
    c = "\n".join(lines)
    return StreamingResponse(io.BytesIO(c.encode("utf-8")),media_type="text/plain",headers={"Content-Disposition":f"attachment; filename={recording.title}.txt"})

@router.get("/{recording_id}/srt")
async def export_srt(recording_id: str, db: Session = Depends(get_db)):
    recording = db.execute(select(Recording).where(Recording.id==recording_id)).scalar_one_or_none()
    if not recording: raise HTTPException(404,"录音不存在")
    tl = db.execute(select(Transcript).where(Transcript.recording_id==recording_id).order_by(Transcript.start_time)).scalars().all()
    lines = []
    for i,t in enumerate(tl,1):
        sp = t.speaker_name or t.speaker
        lines.append(f"{i}\n{_srt(t.start_time)} --> {_srt(t.end_time)}\n{sp}: {t.content}\n")
    c = "\n".join(lines)
    return StreamingResponse(io.BytesIO(c.encode("utf-8")),media_type="text/plain",headers={"Content-Disposition":f"attachment; filename={recording.title}.srt"})
