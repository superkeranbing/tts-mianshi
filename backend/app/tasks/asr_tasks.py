"""Celery tasks for ASR transcription, conversation summary, and QA extraction"""

import json
import logging
import asyncio

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.recording import Recording
from app.models.transcript import Transcript

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=30)
def transcribe_audio_task(self, recording_id: str):
    """Transcribe audio, then generate summary and QA pairs."""
    logger.info(f"Transcribe task started: recording_id={recording_id}")
    db = SessionLocal()
    try:
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return {"error": "Recording not found"}

        recording.status = "processing"
        db.commit()

        from app.services.asr_engine import asr_engine
        segments = asyncio.run(asr_engine.transcribe(recording.audio_path))

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
        logger.info(f"Transcription done: {len(segments)} segments")

        if not segments:
            return {"status": "completed", "segments": 0}

        from app.services.llm_service import llm_service

        tdata = [
            {"speaker": t.speaker, "speaker_name": t.speaker_name, "content": t.content}
            for t in db.query(Transcript)
            .filter(Transcript.recording_id == recording_id)
            .order_by(Transcript.start_time)
            .all()
        ]

        try:
            recording.summary_json = json.dumps(
                asyncio.run(llm_service.summarize_conversation(tdata)),
                ensure_ascii=False,
            )
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")

        try:
            recording.qa_json = json.dumps(
                asyncio.run(llm_service.extract_qa_pairs(tdata)),
                ensure_ascii=False,
            )
        except Exception as e:
            logger.error(f"QA extraction failed: {e}")

        db.commit()
        return {"status": "completed", "segments": len(segments)}

    except Exception as exc:
        logger.error(f"Transcription failed for {recording_id}: {exc}", exc_info=True)
        try:
            rec = db.query(Recording).filter(Recording.id == recording_id).first()
            if rec:
                rec.status = "failed"
                db.commit()
        except Exception:
            db.rollback()
        raise self.retry(exc=exc)

    finally:
        db.close()
