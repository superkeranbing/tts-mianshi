"""模拟 LLM 服务 - 生产环境接入 DeepSeek/Qwen/GPT"""
import json
from typing import Optional

class LLMService:
    def __init__(self, base_url: str = "", api_key: str = "", model: str = ""):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    async def analyze_interview(
        self, transcripts: list[dict], resume_text: Optional[str] = None
    ) -> dict:
        """分析面试转写，提取问答对、评分、知识点。"""
        return {
            "overall_score": 78,
            "strengths": [
                "项目经验描述清晰，STAR法则运用较好",
                "基础技术问题回答准确，React/JS基础扎实"
            ],
            "weaknesses": [
                "系统设计类问题回答不够结构化",
                "缺少量化成果支撑"
            ],
            "improvement_plan": [
                {"week": 1, "focus": "系统设计每日一题"},
                {"week": 2, "focus": "行为面试STAR法则练习"},
                {"week": 3, "focus": "技术深度专题复习"}
            ],
            "summary": "整体表现良好，基础扎实但需加强系统设计能力和量化表达。",
            "qa_pairs": [
                {
                    "question": "请简单介绍一下你自己。",
                    "category": "自我介绍",
                    "your_answer": "我叫张三，毕业于XX大学…",
                    "best_answer": "建议用「过去-现在-未来」框架组织自我介绍…",
                    "score": 72,
                    "improvement": "结构清晰但缺乏亮点数据。"
                },
                {
                    "question": "React的虚拟DOM原理是什么？",
                    "category": "技术问题",
                    "your_answer": "虚拟DOM是React的核心优化机制…",
                    "best_answer": "虚拟DOM使用JS对象描述UI…包括Diff算法(O(n))…Fiber可中断渲染…",
                    "score": 75,
                    "improvement": "可从Reconciliation算法和Fiber架构补充。"
                },
                {
                    "question": "你在项目中遇到的最大技术挑战？",
                    "category": "项目经验",
                    "your_answer": "大数据列表渲染性能问题…",
                    "best_answer": "S-数据规模T-性能指标A-虚拟滚动方案R-渲染时间从3s降到200ms",
                    "score": 68,
                    "improvement": "缺少量化结果，建议用STAR法则重构。"
                },
                {
                    "question": "你的职业规划是什么？",
                    "category": "职业规划",
                    "your_answer": "计划3年内成为全栈架构师…",
                    "best_answer": "短期深耕前端，中期承担架构角色，长期成为领域专家。",
                    "score": 70,
                    "improvement": "可更具体，建议加上与所面试公司的契合分析。"
                }
            ],
            "knowledge_points": [
                {
                    "title": "React 虚拟DOM",
                    "category": "前端技术",
                    "key_concepts": ["Virtual DOM", "Reconciliation", "Diff算法", "Fiber"],
                    "content": "虚拟DOM是React核心优化机制。通过JS对象模拟DOM，在内存中Diff比较后批量更新真实DOM，减少reflow/repaint。Fiber引入了可中断的异步渲染。",
                    "resources": [
                        {"title": "React Reconciliation", "url": "https://react.dev/learn/preserving-and-resetting-state"}
                    ],
                    "interview_tips": [
                        "为什么需要虚拟DOM？直接操作DOM的问题？",
                        "Diff算法三个前提假设是什么？",
                        "Fiber解决了什么问题？"
                    ]
                },
                {
                    "title": "STAR法则",
                    "category": "面试技巧",
                    "key_concepts": ["Situation", "Task", "Action", "Result"],
                    "content": "STAR法则是结构化行为面试回答方法：Situation描述背景，Task明确任务，Action详述行动，Result展示量化结果。",
                    "resources": [],
                    "interview_tips": [
                        "回答控制在2分钟内",
                        "结果必须量化",
                        "强调'我'而非'我们'"
                    ]
                }
            ]
        }

    async def parse_resume(self, raw_text: str) -> dict:
        """解析简历文本，提取结构化信息"""
        return {
            "name": "张三",
            "education": [{"school": "XX大学", "degree": "本科", "major": "计算机科学"}],
            "experience": [
                {"company": "某科技公司", "role": "高级前端", "years": "2020-2025"},
                {"company": "某互联网公司", "role": "前端", "years": "2018-2020"}
            ],
            "skills": ["React", "Vue", "TypeScript", "Node.js"],
            "projects": [{"name": "中后台系统", "description": "大型管理系统", "highlights": ["性能优化"]}]
        }

    async def generate_answer(self, question: str, resume_data: dict, category: str = "technical") -> str:
        """结合简历生成最佳面试答案"""
        return f"针对「{question}」，建议结合你的{resume_data.get('skills',[])[:2]}经验，用STAR法则结构化回答…"


llm_service = LLMService()
