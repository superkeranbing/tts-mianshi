from app.core.celery_app import celery_app

@celery_app.task(bind=True, name="tasks.transcribe_audio")
def transcribe_audio_task(self, recording_id: str):
    """异步 ASR 转写任务"""
    return {"recording_id": recording_id, "status": "completed", "segments": 8}

@celery_app.task(bind=True, name="tasks.analyze_interview")
def analyze_interview_task(self, recording_id: str, resume_id: str = None):
    """异步面试分析任务"""
    return {"recording_id": recording_id, "status": "completed"}
