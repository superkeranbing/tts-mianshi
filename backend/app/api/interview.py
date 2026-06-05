from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import json
from app.core.database import get_db
from app.core.security import require_user
from app.models.recording import Recording
from app.models.interview import InterviewReport, QAPair, KnowledgePoint
from app.schemas import AnalyzeRequest, InterviewReportResponse, QAPairResponse, KnowledgePointResponse
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/interview", tags=["Interview"])

_MOCK_FALLBACK = {
    "overall_score": 78,
    "strengths": ["项目经验描述清晰，STAR法则运用较好", "基础技术问题回答准确"],
    "weaknesses": ["系统设计类问题回答不够结构化", "行为面试中缺少量化成果"],
    "improvement_plan": [{"week": 1, "focus": "系统设计每日一题"}, {"week": 2, "focus": "行为面试模拟练习"}, {"week": 3, "focus": "技术深度专题复习"}],
    "summary": "整体表现良好，基础扎实但需加强系统设计能力和行为面试结构化表达。",
    "qa_pairs": [
        {"question": "请简单介绍一下你自己。", "category": "自我介绍", "your_answer": "我叫张三...", "best_answer": "用过去-现在-未来框架组织...", "score": 72, "improvement": "结构清晰但缺乏亮点数据。"},
        {"question": "React的虚拟DOM原理？", "category": "技术问题", "your_answer": "虚拟DOM是React的核心优化...", "best_answer": "JS对象描述UI→状态变化→Diff算法→批量更新。Fiber实现了可中断异步渲染。", "score": 75, "improvement": "可从Reconciliation和Fiber角度补充。"},
        {"question": "最大技术挑战？", "category": "项目经验", "your_answer": "大数据列表渲染性能问题...", "best_answer": "STAR: S数据规模T性能指标A虚拟滚动R渲染从3s降到200ms", "score": 68, "improvement": "缺少量化指标，用STAR法则重构。"},
        {"question": "职业规划？", "category": "职业规划", "your_answer": "3年内成为全栈架构师...", "best_answer": "短期深耕技术→中期架构角色→长期领域专家，表达与公司契合点。", "score": 70, "improvement": "可更具体，加上与公司的契合分析。"},
    ],
    "knowledge_points": [
        {"title": "React虚拟DOM", "category": "前端技术", "key_concepts": ["Virtual DOM", "Reconciliation", "Fiber", "Diff算法"], "content": "React核心优化机制。JS对象模拟DOM，Diff后批量更新。Fiber可中断异步渲染。", "resources": [{"title": "React Reconciliation", "url": "https://react.dev/learn/preserving-and-resetting-state"}], "interview_tips": ["为什么需要虚拟DOM？", "Diff算法三个前提假设？", "Fiber解决了什么问题？"]},
        {"title": "STAR法则", "category": "面试技巧", "key_concepts": ["Situation", "Task", "Action", "Result"], "content": "结构化行为面试回答方法。每回答控制在2分钟内，结果必须量化。", "resources": [], "interview_tips": ["回答控制在2分钟内", "结果必须量化", "强调'我'而非'我们'"]},
    ],
}


@router.post("/analyze")
async def create_analysis(req: AnalyzeRequest, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    recording = db.execute(
        select(Recording).where(Recording.id == req.recording_id, Recording.user_id == user["id"])
    ).scalar_one_or_none()
    if not recording:
        raise HTTPException(404, "录音不存在")

    # Return existing report if already analyzed with same recording + resume
    conditions = [InterviewReport.recording_id == req.recording_id]
    if req.resume_id:
        conditions.append(InterviewReport.resume_id == req.resume_id)
    existing = db.execute(
        select(InterviewReport).where(and_(*conditions)).limit(1)
    ).scalar_one_or_none()
    if existing:
        return {"report_id": existing.id, "status": "completed", "cached": True}

    # Collect transcripts for LLM analysis
    from app.models.transcript import Transcript
    transcripts = db.execute(
        select(Transcript).where(Transcript.recording_id == req.recording_id).order_by(Transcript.start_time)
    ).scalars().all()

    transcript_data = [
        {"speaker": t.speaker, "speaker_name": t.speaker_name, "content": t.content}
        for t in transcripts
    ]

    # Get resume text if available
    resume_text = None
    if req.resume_id:
        from app.models.resume import Resume
        resume = db.execute(
            select(Resume).where(Resume.id == req.resume_id, Resume.user_id == user["id"])
        ).scalar_one_or_none()
        if resume:
            resume_text = resume.raw_text

    # Call LLM (real API or mock)
    analysis = await llm_service.analyze_interview(transcript_data, resume_text)

    # Save report
    report = InterviewReport(
        user_id=user["id"],
        recording_id=req.recording_id,
        resume_id=req.resume_id,
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
    return {"report_id": report.id, "status": "completed"}


@router.get("/reports", response_model=list[InterviewReportResponse])
async def list_reports(db: Session = Depends(get_db), user: dict = Depends(require_user)):
    reports = db.execute(
        select(InterviewReport).where(InterviewReport.user_id == user["id"]).order_by(InterviewReport.created_at.desc())
    ).scalars().all()
    return [_serialize(r) for r in reports]


@router.get("/reports/{report_id}", response_model=InterviewReportResponse)
async def get_report(report_id: str, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    report = db.execute(
        select(InterviewReport).where(InterviewReport.id == report_id, InterviewReport.user_id == user["id"])
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(404, "报告不存在")
    return _serialize(report)


def _normalize_kp_resources(data: list) -> list[dict]:
    """Normalize knowledge point resources to list[dict] format"""
    if not data:
        return []
    result = []
    for item in data:
        if isinstance(item, dict):
            result.append(item)
        elif isinstance(item, str):
            result.append({"title": item, "url": ""})
        else:
            result.append({"title": str(item), "url": ""})
    return result


def _serialize(r: InterviewReport) -> InterviewReportResponse:
    return InterviewReportResponse(
        id=r.id, recording_id=r.recording_id, resume_id=r.resume_id,
        overall_score=r.overall_score,
        strengths=json.loads(r.strengths_json) if r.strengths_json else [],
        weaknesses=json.loads(r.weaknesses_json) if r.weaknesses_json else [],
        improvement_plan=json.loads(r.improvement_plan_json) if r.improvement_plan_json else [],
        summary=r.summary,
        qa_pairs=[QAPairResponse(id=qa.id, question=qa.question, question_category=qa.question_category, your_answer=qa.your_answer, best_answer=qa.best_answer, answer_score=qa.answer_score, improvement_suggestions=qa.improvement_suggestions) for qa in r.qa_pairs],
        knowledge_points=[KnowledgePointResponse(id=kp.id, title=kp.title, category=kp.category, key_concepts=json.loads(kp.key_concepts_json) if kp.key_concepts_json else [], content=kp.content, resources=_normalize_kp_resources(json.loads(kp.resources_json)) if kp.resources_json else [], interview_tips=json.loads(kp.interview_tips_json) if kp.interview_tips_json else []) for kp in r.knowledge_points],
        created_at=r.created_at,
    )