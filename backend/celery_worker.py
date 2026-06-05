"""Celery worker entry point

Usage:
  celery -A backend.celery_worker worker -l info
"""
import os
import sys
# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_app import celery_app
# Import tasks to register them
from app.tasks import transcribe_audio_task, analyze_interview_task

if __name__ == "__main__":
    celery_app.start()