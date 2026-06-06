"""Celery tasks for interview analysis"""

import json
import logging
import asyncio

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.interview import InterviewReport, QAPair, KnowledgePoint
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.resume import Resume

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=1, default_retry_delay=30)
def analyze_interview_task(self, report_id: str):
    """Run full interview analysis: collect transcripts + resume, call LLM, save results."""
    logger.info(f"Interview analysis task started: report_id={report_id}")
    db = SessionLocal()
    try:
        report = db.query(InterviewReport).filter(InterviewReport.id == report_id).first()
        if not report:
            logger.error(f"Report {report_id} not found")
            return {"error": "Report not found"}

        report.status = "processing"
        db.commit()

        transcripts = (
            db.query(Transcript)
            .filter(Transcript.recording_id == report.recording_id)
            .order_by(Transcript.start_time)
            .all()
        )
        transcript_data = [
            {"speaker": t.speaker, "speaker_name": t.speaker_name, "content": t.content}
            for t in transcripts
        ]

        resume_text = None
        if report.resume_id:
            resume = db.query(Resume).filter(Resume.id == report.resume_id).first()
            if resume:
                # Use cached text if available, otherwise extract on demand
                if resume.raw_text and resume.raw_text.strip():
                    resume_text = resume.raw_text
                elif resume.file_path:
                    try:
                        from app.services.resume_parser import resume_parser
                        if resume.file_type == "pdf":
                            resume_text = asyncio.run(resume_parser._parse_pdf(resume.file_path))
                        elif resume.file_type in ("doc", "docx"):
                            resume_text = asyncio.run(resume_parser._parse_docx(resume.file_path))
                        if resume_text:
                            resume.raw_text = resume_text
                            db.commit()
                    except Exception as e:
                        logger.error(f"Resume text extraction failed: {e}")

        from app.services.llm_service import llm_service
        analysis = asyncio.run(llm_service.analyze_interview(transcript_data, resume_text))

        report.overall_score = analysis.get("overall_score")
        report.strengths_json = json.dumps(analysis.get("strengths", []), ensure_ascii=False)
        report.weaknesses_json = json.dumps(analysis.get("weaknesses", []), ensure_ascii=False)
        report.improvement_plan_json = json.dumps(
            analysis.get("improvement_plan", []), ensure_ascii=False
        )
        report.summary = analysis.get("summary")
        report.status = "completed"
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
        logger.info(f"Interview analysis completed: report_id={report_id}")
        return {"status": "completed", "overall_score": report.overall_score}

    except Exception as exc:
        logger.error(f"Interview analysis failed for {report_id}: {exc}", exc_info=True)
        try:
            rep = db.query(InterviewReport).filter(InterviewReport.id == report_id).first()
            if rep:
                rep.status = "failed"
                db.commit()
        except Exception:
            db.rollback()
        raise self.retry(exc=exc)

    finally:
        db.close()
