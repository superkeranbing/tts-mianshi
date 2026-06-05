"""Development runner -- starts FastAPI + Celery worker side by side.

Run:
  python run.py              # both FastAPI + Celery worker
  python run.py --api-only   # FastAPI only (start Celery separately)
  python run.py --celery-only # Celery worker only
"""
import sys
import os
import subprocess
import argparse
import time

def start_uvicorn():
    import uvicorn
    print("[run] Starting FastAPI on http://0.0.0.0:8000")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")

def start_celery():
    print("[run] Starting Celery worker...")
    worker_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "celery_worker.py")
    proc = subprocess.Popen(
        [sys.executable, "-m", "celery", "-A", "celery_worker", "worker",
         "-l", "info", "-P", "solo", "--without-gossip", "--without-mingle",
         "--without-heartbeat"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    return proc

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-only", action="store_true", help="Start FastAPI only")
    parser.add_argument("--celery-only", action="store_true", help="Start Celery worker only")
    args = parser.parse_args()

    if args.api_only:
        start_uvicorn()
    elif args.celery_only:
        proc = start_celery()
        proc.wait()
    else:
        celery_proc = start_celery()
        print("[run] Both services started. Press Ctrl+C to stop.")
        try:
            start_uvicorn()
        except KeyboardInterrupt:
            pass
        finally:
            celery_proc.terminate()
            celery_proc.wait()
            print("[run] Stopped.")
