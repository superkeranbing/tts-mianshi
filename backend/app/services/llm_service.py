"""LLM 服务 - 支持 DeepSeek / Qwen / OpenAI 兼容 API，无 API key 时回退 mock"""

import json, httpx, logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

INTERVIEW_SYSTEM_PROMPT = """你是一位资深面试教练和职业顾问。分析以下面试对话，输出严格的JSON格式结果。

要求：
1. 从对话中提取所有面试官的问题和被面试者的回答
2. 对每个问题：归类(自我介绍/技术问题/项目经验/行为面试/职业规划/薪资期望)、评分(0-100)、写出最佳答案、给改进建议
3. 评估整体表现：综合评分(0-100)、优势列表、待提升列表
4. 设计相关知识点卡片(含关键概念、推荐资源、面试要点)
5. 制定3周提升计划
6. 写一段100字以内总结

输出纯JSON，格式如下：
{
  "overall_score": 78,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "improvement_plan": [{"week": 1, "focus": "..."}, ...],
  "summary": "...",
  "qa_pairs": [{"question": "...", "category": "...", "your_answer": "...", "best_answer": "...", "score": 75, "improvement": "..."}],
  "knowledge_points": [{"title": "...", "category": "...", "key_concepts": ["..."], "content": "...", "resources": [], "interview_tips": ["..."]}]
}"""


class LLMService:
    def __init__(self):
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS

    def _is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "sk-placeholder")

    async def _call_api(self, system_prompt: str, user_prompt: str) -> dict:
        """Call DeepSeek/Qwen API with chat completions format"""
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

    async def analyze_interview(
        self, transcripts: list[dict], resume_text: Optional[str] = None
    ) -> dict:
        # Build transcript text
        lines = []
        for t in transcripts:
            speaker = t.get("speaker_name") or t.get("speaker", "未知")
            lines.append(f"{speaker}: {t.get('content', '')}")
        transcript_text = "\n".join(lines)

        user_prompt = f"面试对话记录：\n{transcript_text}"
        if resume_text:
            user_prompt += f"\n\n候选人简历：\n{resume_text}"

        # Try real API
        if self._is_configured():
            try:
                logger.info(f"Calling LLM API: {self.model}")
                return await self._call_api(INTERVIEW_SYSTEM_PROMPT, user_prompt)
            except Exception as e:
                logger.error(f"LLM API failed: {e}, falling back to mock")

        # Mock fallback
        return _MOCK_ANALYSIS

    async def parse_resume(self, raw_text: str) -> dict:
        if self._is_configured():
            try:
                prompt = f"解析以下简历，提取结构化信息，输出JSON：\n{raw_text}"
                return await self._call_api(
                    "你是简历解析专家。从文本中提取：name, education(学校/学位/专业数组), experience(公司/职位/年限数组), skills(技能数组), projects(名称/描述/亮点数组)。输出纯JSON。",
                    prompt,
                )
            except Exception as e:
                logger.error(f"Resume parsing failed: {e}")

        return {
            "name": "", "education": [], "experience": [],
            "skills": [], "projects": [],
        }

    async def generate_answer(
        self, question: str, resume_data: dict, category: str = "technical"
    ) -> str:
        if self._is_configured():
            try:
                prompt = f"问题：{question}\n简历：{json.dumps(resume_data, ensure_ascii=False)}\n请生成最佳回答。"
                result = await self._call_api(
                    "你是一位面试教练。根据简历和问题生成最佳面试回答，用STAR法则。",
                    prompt,
                )
                return result.get("answer", "")
            except Exception as e:
                logger.error(f"Answer generation failed: {e}")
        return "（请配置LLM_API_KEY以生成个性化答案）"


# Mock data for fallback
_MOCK_ANALYSIS = {
    "overall_score": 78,
    "strengths": [
        "项目经验描述清晰，STAR法则运用较好",
        "基础技术问题回答准确",
        "沟通表达自然流畅",
    ],
    "weaknesses": [
        "系统设计类问题回答不够结构化",
        "行为面试中缺少量化成果",
        "部分技术深度问题可更深入",
    ],
    "improvement_plan": [
        {"week": 1, "focus": "系统设计每日一题"},
        {"week": 2, "focus": "行为面试模拟练习"},
        {"week": 3, "focus": "技术深度专题复习"},
    ],
    "summary": "整体表现良好，基础扎实但需加强系统设计能力和行为面试结构化表达。",
    "qa_pairs": [
        {
            "question": "请简单介绍一下你自己。",
            "category": "自我介绍",
            "your_answer": "我叫张三，毕业于XX大学…",
            "best_answer": "建议用「过去-现在-未来」框架：教育背景和核心技能→当前工作亮点成果→对职位的兴趣和匹配度。",
            "score": 72,
            "improvement": "结构清晰但缺乏亮点数据，建议补充具体的项目成果数字。",
        },
        {
            "question": "React的虚拟DOM原理是什么？",
            "category": "技术问题",
            "your_answer": "虚拟DOM是React的核心优化机制…",
            "best_answer": "虚拟DOM用JS对象描述UI结构，状态变化生成新虚拟DOM树，通过Diff算法(O(n))比较新旧树，批量更新真实DOM。Fiber架构进一步实现了可中断的异步渲染。",
            "score": 75,
            "improvement": "可从Reconciliation算法和Fiber可中断渲染角度补充。",
        },
        {
            "question": "你在项目中遇到的最大技术挑战？",
            "category": "项目经验",
            "your_answer": "大数据量列表渲染性能问题…",
            "best_answer": "用STAR法则：S-数据规模，T-性能指标，A-虚拟滚动方案，R-渲染时间从3s降到200ms。",
            "score": 68,
            "improvement": "缺少量化指标，用STAR法则重构。",
        },
        {
            "question": "未来的职业规划？",
            "category": "职业规划",
            "your_answer": "3年内成为全栈架构师…",
            "best_answer": "分阶段：短期深耕技术，中期承担架构角色，长期成为领域专家，表达与公司发展契合点。",
            "score": 70,
            "improvement": "可更具体，加上与所面试公司的契合分析。",
        },
    ],
    "knowledge_points": [
        {
            "title": "React虚拟DOM",
            "category": "前端技术",
            "key_concepts": ["Virtual DOM", "Reconciliation", "Fiber", "Diff算法"],
            "content": "虚拟DOM是React的核心优化机制。通过JS对象模拟DOM，内存中Diff比较后批量更新真实DOM，减少reflow/repaint。Fiber引入可中断异步渲染。",
            "resources": [{"title": "React Reconciliation", "url": "https://react.dev/learn/preserving-and-resetting-state"}],
            "interview_tips": ["为什么需要虚拟DOM？", "Diff算法三个前提假设？", "Fiber解决了什么问题？"],
        },
        {
            "title": "STAR法则",
            "category": "面试技巧",
            "key_concepts": ["Situation", "Task", "Action", "Result"],
            "content": "STAR法则：Situation描述背景，Task明确任务，Action详述行动，Result展示量化结果。每个回答控制在2分钟内。",
            "resources": [],
            "interview_tips": ["回答控制在2分钟内", "结果必须量化", "强调'我'而非'我们'"],
        },
    ],
}


llm_service = LLMService()
