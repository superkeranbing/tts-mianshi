from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from app.config import get_settings
from app.core.database import init_db
from app.api import auth, recording, asr, interview, export, websocket, resume

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(recording.router)
app.include_router(asr.router)
app.include_router(interview.router)
app.include_router(export.router)
app.include_router(websocket.router)
app.include_router(resume.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str = ""):
    if full_path:
        target = os.path.join(frontend_dir, full_path)
        if os.path.isfile(target):
            mt = "application/javascript" if target.endswith((".mjs", ".module.js")) else None
            return FileResponse(target, media_type=mt)
    return FileResponse(os.path.join(frontend_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
