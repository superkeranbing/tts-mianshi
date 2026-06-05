"""Celery async tasks for ASR transcription and interview analysis"""
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.interview import InterviewReport, QAPair, KnowledgePoint
from app.services.asr_engine import asr_engine
from app.services.llm_service import llm_service
import json, asyncio, logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.transcribe_audio", max_retries=3, default_retry_delay=30)
def transcribe_audio_task(self, recording_id: str):
    """Real async ASR transcription task with summary + QA generation"""
    logger.info(f"Starting transcription for {recording_id}")
    db = SessionLocal()
    try:
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if not recording:
            logger.error(f"Recording {recording_id} not found")
            return {"error": "Recording not found"}

        recording.status = "processing"
        db.commit()

        # Run ASR engine
        import asyncio
        segments = asyncio.run(asr_engine.transcribe(recording.audio_path))

        # Save results
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
        logger.info(f"Transcription completed for {recording_id}: {len(segments)} segments")

        # Generate summary and QA and cache in DB
        if segments:
            transcript_data = [
                {"speaker": t.speaker, "speaker_name": t.speaker_name, "content": t.content}
                for t in db.query(Transcript)
                .filter(Transcript.recording_id == recording_id)
                .order_by(Transcript.start_time).all()
            ]
            try:
                summary_result = asyncio.run(llm_service.summarize_conversation(transcript_data))
                recording.summary_json = json.dumps(summary_result, ensure_ascii=False)
                logger.info(f"Summary generated for {recording_id}")
            except Exception as e:
                logger.error(f"Summary generation failed for {recording_id}: {e}")

            try:
                qa_result = asyncio.run(llm_service.extract_qa_pairs(transcript_data))
                recording.qa_json = json.dumps(qa_result, ensure_ascii=False)
                logger.info(f"QA extracted for {recording_id}")
            except Exception as e:
                logger.error(f"QA extraction failed for {recording_id}: {e}")

            db.commit()

        return {"recording_id": recording_id, "status": "completed", "segments": len(segments)}

    except Exception as e:
        logger.error(f"Transcription failed for {recording_id}: {e}")
        try:
            rec = db.query(Recording).filter(Recording.id == recording_id).first()
            if rec:
                rec.status = "failed"
                db.commit()
        except:
            pass
        raise self.retry(exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, name="tasks.analyze_interview", max_retries=2, default_retry_delay=15)
def analyze_interview_task(self, recording_id: str, resume_id: str = None, user_id: str = "default"):
    """Real async interview analysis task"""
    logger.info(f"Starting interview analysis for {recording_id}")
    db = SessionLocal()
    try:
        transcripts = db.query(Transcript).filter(Transcript.recording_id == recording_id).order_by(Transcript.start_time).all()
        transcript_data = [
            {"speaker": t.speaker, "speaker_name": t.speaker_name, "content": t.content}
            for t in transcripts
        ]

        resume_text = None
        if resume_id:
            from app.models.resume import Resume
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if resume:
                resume_text = resume.raw_text

        import asyncio
        analysis = asyncio.run(llm_service.analyze_interview(transcript_data, resume_text))

        report = InterviewReport(
            user_id=user_id,
            recording_id=recording_id,
            resume_id=resume_id,
            overall_score=analysis.get("overall_score"),
            strengths_json=json.dumps(analysis.get("strengths", []), ensure_ascii=False),
            weaknesses_json=json.dumps(analysis.get("weaknesses", []), ensure_ascii=False),
            improvement_plan_json=json.dumps(analysis.get("improvement_plan", []), ensure_ascii=False),
            summary=analysis.get("summary"),
        )
        db.add(report)
        db.flush()

        for qa in analysis.get("qa_pairs", []):
            db.add(QAPair(
                report_id=report.id,
                question=qa.get("question", ""),
                question_category=qa.get("category", ""),
                your_answer=qa.get("your_answer", ""),
                best_answer=qa.get("best_answer", ""),
                answer_score=qa.get("score", qa.get("answer_score")),
                improvement_suggestions=qa.get("improvement", qa.get("improvement_suggestions")),
            ))

        for kp in analysis.get("knowledge_points", []):
            db.add(KnowledgePoint(
                report_id=report.id,
                title=kp.get("title", ""),
                category=kp.get("category", ""),
                key_concepts_json=json.dumps(kp.get("key_concepts", []), ensure_ascii=False),
                content=kp.get("content", ""),
                resources_json=json.dumps(kp.get("resources", []), ensure_ascii=False),
                interview_tips_json=json.dumps(kp.get("interview_tips", []), ensure_ascii=False),
            ))
        db.commit()
        logger.info(f"Analysis completed for {recording_id}: report_id={report.id}")
        return {"report_id": report.id, "status": "completed"}

    except Exception as e:
        logger.error(f"Analysis failed for {recording_id}: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()