from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import require_user
from app.models.recording import Recording

router = APIRouter(prefix="/api/asr", tags=["ASR"])


@router.post("/{recording_id}/transcribe")
async def trigger_transcribe(recording_id: str, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    recording = db.execute(
        select(Recording).where(Recording.id == recording_id, Recording.user_id == user["id"])
    ).scalar_one_or_none()
    if not recording:
        raise HTTPException(404, "录音不存在")

    if recording.status == "completed":
        return {"status": "completed", "message": "Already transcribed"}

    # Dispatch Celery task for async transcription
    from app.tasks import transcribe_audio_task
    task = transcribe_audio_task.delay(recording_id)

    recording.status = "processing"
    db.commit()

    return {"status": "processing", "task_id": task.id, "message": "Transcription started"}


@router.get("/{recording_id}/status")
async def get_status(recording_id: str, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    recording = db.execute(
        select(Recording).where(Recording.id == recording_id, Recording.user_id == user["id"])
    ).scalar_one_or_none()
    if not recording:
        raise HTTPException(404, "录音不存在")
    return {"status": recording.status}