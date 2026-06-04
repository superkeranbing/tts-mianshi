from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import json
from app.core.database import get_db
from app.models.recording import Recording
from app.models.interview import InterviewReport, QAPair, KnowledgePoint
from app.schemas import AnalyzeRequest, InterviewReportResponse, QAPairResponse, KnowledgePointResponse

router = APIRouter(prefix="/api/interview", tags=["Interview"])

MOCK_A = {
    "overall_score":78,
    "strengths":["项目经验描述清晰，STAR法则运用较好","基础技术问题回答准确","沟通表达自然流畅"],
    "weaknesses":["系统设计类问题回答不够结构化","行为面试中缺少量化成果","部分技术深度问题可更深入"],
    "improvement_plan":[{"week":1,"focus":"系统设计每日一题"},{"week":2,"focus":"行为面试模拟练习"},{"week":3,"focus":"技术深度专题复习"}],
    "summary":"整体表现良好，基础扎实但需加强系统设计能力和行为面试结构化表达。建议多练习STAR法则，积累量化成果描述。",
    "qa_pairs":[
        {"question":"请简单介绍一下你自己。","category":"自我介绍","your_answer":"我叫张三，毕业于XX大学…","best_answer":"建议用「过去-现在-未来」框架：先说教育背景和核心技能，再讲亮点成果（用数据说话），最后表达工作兴趣。","score":72,"improvement":"结构清晰但缺乏亮点数据，补充具体项目成果数字。"},
        {"question":"React的虚拟DOM原理是什么？","category":"技术问题","your_answer":"虚拟DOM是React的核心优化机制…","best_answer":"虚拟DOM用JS对象描述UI结构，状态变化生成新树，通过Diff算法(O(n))比较，批量更新真实DOM。Fiber架构引入可中断异步渲染。","score":75,"improvement":"可从Reconciliation算法和Fiber可中断渲染角度补充。"},
        {"question":"你在项目中遇到的最大技术挑战？","category":"项目经验","your_answer":"大数据量列表渲染性能问题…","best_answer":"用STAR法则：S-数据规模，T-性能指标，A-虚拟滚动方案，R-渲染时间从3s降到200ms。","score":68,"improvement":"缺少量化指标，用STAR法则重构。"},
        {"question":"未来的职业规划？","category":"职业规划","your_answer":"3年内成为全栈架构师…","best_answer":"分阶段：短期深耕技术，中期承担架构角色，长期成为领域专家，表达与公司发展契合点。","score":70,"improvement":"可更具体，加上与面试公司的契合分析。"}
    ],
    "knowledge_points":[
        {"title":"React虚拟DOM","category":"前端技术","key_concepts":["VirtualDOM","Reconciliation","Fiber","Diff算法"],"content":"虚拟DOM是React核心优化机制。通过JS对象模拟DOM，内存中Diff比较后批量更新真实DOM，减少reflow/repaint。Fiber引入可中断异步渲染。","resources":[{"title":"React Reconciliation","url":"https://react.dev/learn/preserving-and-resetting-state"}],"interview_tips":["为什么需要虚拟DOM？","Diff算法三个前提假设？","Fiber解决了什么问题？"]},
        {"title":"STAR法则","category":"面试技巧","key_concepts":["Situation","Task","Action","Result"],"content":"STAR法则：Situation描述背景，Task明确任务，Action详述行动，Result展示量化结果。每个回答控制在2分钟内，结果必须量化。","resources":[],"interview_tips":["回答控制在2分钟内","结果必须量化","强调'我'而非'我们'"]}
    ]
}

@router.post("/analyze")
async def create_analysis(req: AnalyzeRequest, db: Session = Depends(get_db)):
    recording = db.execute(select(Recording).where(Recording.id==req.recording_id)).scalar_one_or_none()
    if not recording: raise HTTPException(404,"录音不存在")
    report = InterviewReport(user_id="default",recording_id=req.recording_id,resume_id=req.resume_id,overall_score=MOCK_A["overall_score"],strengths_json=json.dumps(MOCK_A["strengths"],ensure_ascii=False),weaknesses_json=json.dumps(MOCK_A["weaknesses"],ensure_ascii=False),improvement_plan_json=json.dumps(MOCK_A["improvement_plan"],ensure_ascii=False),summary=MOCK_A["summary"])
    db.add(report)
    db.flush()
    for qa in MOCK_A["qa_pairs"]:
        db.add(QAPair(report_id=report.id,question=qa["question"],question_category=qa["category"],your_answer=qa["your_answer"],best_answer=qa["best_answer"],answer_score=qa["score"],improvement_suggestions=qa["improvement"]))
    for kp in MOCK_A["knowledge_points"]:
        db.add(KnowledgePoint(report_id=report.id,title=kp["title"],category=kp["category"],key_concepts_json=json.dumps(kp["key_concepts"],ensure_ascii=False),content=kp["content"],resources_json=json.dumps(kp["resources"],ensure_ascii=False),interview_tips_json=json.dumps(kp["interview_tips"],ensure_ascii=False)))
    db.commit()
    return {"report_id":report.id,"status":"completed"}

@router.get("/reports",response_model=list[InterviewReportResponse])
async def list_reports(db: Session = Depends(get_db)):
    reports = db.execute(select(InterviewReport).order_by(InterviewReport.created_at.desc())).scalars().all()
    return [_serialize(r) for r in reports]

@router.get("/reports/{report_id}",response_model=InterviewReportResponse)
async def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.execute(select(InterviewReport).where(InterviewReport.id==report_id)).scalar_one_or_none()
    if not report: raise HTTPException(404,"报告不存在")
    return _serialize(report)

def _serialize(r):
    return InterviewReportResponse(
        id=r.id,recording_id=r.recording_id,resume_id=r.resume_id,overall_score=r.overall_score,
        strengths=json.loads(r.strengths_json) if r.strengths_json else [],
        weaknesses=json.loads(r.weaknesses_json) if r.weaknesses_json else [],
        improvement_plan=json.loads(r.improvement_plan_json) if r.improvement_plan_json else [],
        summary=r.summary,
        qa_pairs=[QAPairResponse(id=qa.id,question=qa.question,question_category=qa.question_category,your_answer=qa.your_answer,best_answer=qa.best_answer,answer_score=qa.answer_score,improvement_suggestions=qa.improvement_suggestions) for qa in r.qa_pairs],
        knowledge_points=[KnowledgePointResponse(id=kp.id,title=kp.title,category=kp.category,key_concepts=json.loads(kp.key_concepts_json) if kp.key_concepts_json else [],content=kp.content,resources=json.loads(kp.resources_json) if kp.resources_json else [],interview_tips=json.loads(kp.interview_tips_json) if kp.interview_tips_json else []) for kp in r.knowledge_points],
        created_at=r.created_at
    )
