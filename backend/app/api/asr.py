from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import random
from app.core.database import get_db
from app.models.recording import Recording
from app.models.transcript import Transcript

router = APIRouter(prefix="/api/asr", tags=["ASR"])

MOCK = [
    {"speaker":"面试官","speaker_name":"面试官","content":"请简单介绍一下你自己。","start":0,"end":3.5},
    {"speaker":"候选人","speaker_name":"张三","content":"面试官好，我叫张三，毕业于XX大学计算机专业，有5年前端开发经验…","start":4,"end":18},
    {"speaker":"面试官","speaker_name":"面试官","content":"能详细说说 React 的虚拟 DOM 原理吗？","start":20,"end":25},
    {"speaker":"候选人","speaker_name":"张三","content":"虚拟DOM是React的核心优化机制，它用JS对象模拟真实DOM结构...","start":26,"end":52},
    {"speaker":"面试官","speaker_name":"面试官","content":"你在项目中遇到的最大技术挑战是什么？","start":54,"end":58},
    {"speaker":"候选人","speaker_name":"张三","content":"我们面临大数据量列表渲染性能问题，采用虚拟滚动方案优化...","start":59,"end":85},
    {"speaker":"面试官","speaker_name":"面试官","content":"未来的职业规划？","start":87,"end":90},
    {"speaker":"候选人","speaker_name":"张三","content":"希望3年内成为全栈架构师，深耕前端并拓展后端能力。","start":91,"end":110},
]

@router.post("/{recording_id}/transcribe")
async def trigger_transcribe(recording_id: str, db: Session = Depends(get_db)):
    recording = db.execute(select(Recording).where(Recording.id==recording_id)).scalar_one_or_none()
    if not recording: raise HTTPException(404,"录音不存在")
    recording.audio_duration = MOCK[-1]["end"]
    recording.status = "completed"
    for seg in MOCK:
        db.add(Transcript(recording_id=recording_id,speaker=seg["speaker"],speaker_name=seg["speaker_name"],content=seg["content"],start_time=seg["start"],end_time=seg["end"],confidence=random.uniform(0.85,0.99)))
    db.commit()
    return {"status":"completed","segments":len(MOCK)}

@router.get("/{recording_id}/status")
async def get_status(recording_id: str, db: Session = Depends(get_db)):
    recording = db.execute(select(Recording).where(Recording.id==recording_id)).scalar_one_or_none()
    if not recording: raise HTTPException(404,"录音不存在")
    return {"status":recording.status}
