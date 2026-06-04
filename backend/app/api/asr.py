from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import random
from app.core.database import get_db
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.services.asr_engine import asr_engine

router = APIRouter(prefix="/api/asr", tags=["ASR"])


@router.post("/{recording_id}/transcribe")
async def trigger_transcribe(recording_id: str, db: Session = Depends(get_db)):
    recording = db.execute(select(Recording).where(Recording.id == recording_id)).scalar_one_or_none()
    if not recording:
        raise HTTPException(404, "录音不存在")

    # Real ASR pipeline: audio → VAD → ASR → diarization
    segments = await asr_engine.transcribe(recording.audio_path)

    recording.audio_duration = segments[-1].end_time if segments else 0
    recording.status = "completed"

    for seg in segments:
        db.add(Transcript(
            recording_id=recording_id,
            speaker=seg.speaker,
            speaker_name=seg.speaker_name,
            content=seg.content,
            start_time=seg.start_time,
            end_time=seg.end_time,
            confidence=seg.confidence,
        ))

    db.commit()
    return {"status": "completed", "segments": len(segments)}


@router.get("/{recording_id}/status")
async def get_status(recording_id: str, db: Session = Depends(get_db)):
    recording = db.execute(select(Recording).where(Recording.id == recording_id)).scalar_one_or_none()
    if not recording:
        raise HTTPException(404, "录音不存在")
    return {"status": recording.status}
