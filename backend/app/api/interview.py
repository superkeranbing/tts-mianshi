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
    "improvement_plan": [
        {"week": 1, "focus": "系统设计每日一题"},
        {"week": 2, "focus": "行为面试模拟练习"},
        {"week": 3, "focus": "技术深度专题复盘"},
    ],
    "summary": "整体表现良好，基础扎实，但需加强系统设计能力和行为面试中的结构化表达。",
    "qa_pairs": [
        {
            "question": "请简单介绍一下你自己？",
            "category": "自我介绍",
            "your_answer": "我叫张三...",
            "best_answer": "可以用过去-现在-未来框架组织表达，突出优势与目标岗位匹配点。",
            "score": 72,
            "improvement": "结构较清晰，但缺少亮点数据和代表性成果。",
        },
        {
            "question": "React 的虚拟 DOM 原理是什么？",
            "category": "技术问题",
            "your_answer": "虚拟 DOM 是 React 的核心优化之一......",
            "best_answer": "使用 JS 对象描述 UI，状态变化后通过 Diff 算法找出差异，再批量更新真实 DOM。Fiber 实现了可中断的异步渲染。",
            "score": 75,
            "improvement": "可从 Reconciliation 和 Fiber 的角度补充原理与价值。",
        },
        {
            "question": "你经历过的最大技术挑战是什么？",
            "category": "项目经验",
            "your_answer": "大数据列表渲染性能问题...",
            "best_answer": "使用 STAR 表达：说明数据规模、性能目标、优化手段，以及把渲染耗时从 2 秒降到 200ms 的结果。",
            "score": 68,
            "improvement": "缺少量化指标，建议用 STAR 法则重新组织答案。",
        },
        {
            "question": "你的职业规划是什么？",
            "category": "职业规划",
            "your_answer": "3 年内成为全栈架构师......",
            "best_answer": "短期深耕技术，中期承担架构职责，长期成为领域专家，并说明与目标公司的契合点。",
            "score": 70,
            "improvement": "可以更具体一些，补充与目标岗位和公司的匹配分析。",
        },
    ],
    "knowledge_points": [
        {
            "title": "React 虚拟 DOM",
            "category": "前端技术",
            "key_concepts": ["Virtual DOM", "Reconciliation", "Fiber", "Diff 算法"],
            "content": "React 的核心优化机制之一。先用 JS 对象模拟 DOM，再通过 Diff 找出差异并批量更新。Fiber 让渲染具备可中断和可调度能力。",
            "resources": [{"title": "React Reconciliation", "url": "https://react.dev/learn/preserving-and-resetting-state"}],
            "interview_tips": ["为什么需要虚拟 DOM？", "Diff 算法有哪些前提假设？", "Fiber 解决了什么问题？"],
        },
        {
            "title": "STAR 法则",
            "category": "面试技巧",
            "key_concepts": ["Situation", "Task", "Action", "Result"],
            "content": "结构化回答行为面试问题的方法。每次回答尽量控制在 2 分钟内，并确保结果可量化。",
            "resources": [],
            "interview_tips": ["回答尽量控制在 2 分钟内", "结果必须量化", "强调“我”而非“我们”"],
        },
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

    # Create placeholder report, then dispatch Celery task
    report = InterviewReport(
        user_id=user["id"],
        recording_id=req.recording_id,
        resume_id=req.resume_id,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    from app.tasks.interview_tasks import analyze_interview_task
    task = analyze_interview_task.delay(report.id)

    return {"report_id": report.id, "task_id": task.id, "status": "pending"}


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
        status=r.status,
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
