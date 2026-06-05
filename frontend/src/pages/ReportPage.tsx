import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getReport } from "../services/api";
import type { InterviewReport } from "../types";
import { ArrowLeft, Trophy, AlertTriangle, BookOpen, Target, Download } from "lucide-react";
import { exportReportPdf } from "../services/api";

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    getReport(id).then(setReport).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <div className="max-w-5xl mx-auto px-6 py-8 text-center text-red-400">{error}</div>;
  if (!report) return <div className="max-w-5xl mx-auto px-6 py-8 text-center text-gray-500">加载中...</div>;

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <Link to="/interview" className="text-gray-500 hover:text-gray-300"><ArrowLeft className="w-5 h-5" /></Link>
        <h2 className="text-xl font-bold">📊 面试提升报告</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 text-center">
          <p className={`text-5xl font-bold ${(report.overall_score ?? 0) >= 80 ? "text-emerald-400" : (report.overall_score ?? 0) >= 60 ? "text-yellow-400" : "text-red-400"}`}>{report.overall_score ?? "--"}</p>
          <p className="text-sm text-gray-500 mt-2">综合评分 / 100</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 text-center">
          <p className="text-5xl font-bold text-emerald-400">{report.qa_pairs?.length ?? 0}</p>
          <p className="text-sm text-gray-500 mt-2">分析问题数</p>
        </div>
      </div>

      {report.summary && (
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 mb-8">
          <h3 className="font-semibold mb-2">📝 总结</h3>
          <p className="text-sm text-gray-300 leading-relaxed">{report.summary}</p>
        </div>
      )}

      {(report.strengths.length > 0 || report.weaknesses.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
            <h3 className="font-semibold mb-3 text-emerald-400 flex items-center gap-2"><Trophy className="w-4 h-4" /> 优势</h3>
            <ul className="space-y-2">{report.strengths.map((s, i) => <li key={i} className="text-sm text-gray-300 flex gap-2"><span className="text-emerald-400">▸</span> {s}</li>)}</ul>
          </div>
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
            <h3 className="font-semibold mb-3 text-yellow-400 flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> 待提升</h3>
            <ul className="space-y-2">{report.weaknesses.map((w, i) => <li key={i} className="text-sm text-gray-300 flex gap-2"><span className="text-yellow-400">▸</span> {w}</li>)}</ul>
          </div>
        </div>
      )}

      {report.qa_pairs.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">💬 问题分析 ({report.qa_pairs.length} 个问题)</h3>
          <div className="space-y-4">
            {report.qa_pairs.map((qa, i) => (
              <div key={qa.id || i} className="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <div className="flex items-center gap-2 mb-3 flex-wrap">
                  <span className="font-medium">Q{i + 1}: {qa.question}</span>
                  {qa.question_category && <span className="text-xs px-2 py-0.5 bg-gray-800 rounded">{qa.question_category}</span>}
                  {qa.answer_score != null && (
                    <span className={`text-xs ml-auto px-2 py-0.5 rounded ${qa.answer_score >= 80 ? "bg-emerald-900/50 text-emerald-400" : qa.answer_score >= 60 ? "bg-yellow-900/50 text-yellow-400" : "bg-red-900/50 text-red-400"}`}>
                      {qa.answer_score}分
                    </span>
                  )}
                </div>
                {qa.your_answer && <div className="mb-3"><span className="text-xs text-gray-500">🎯 你的回答</span><p className="text-sm text-gray-300 mt-1 bg-gray-800/50 rounded p-3">{qa.your_answer}</p></div>}
                {qa.best_answer && <div className="mb-3"><span className="text-xs text-emerald-400">✅ 最佳答案</span><p className="text-sm text-gray-300 mt-1 bg-emerald-900/10 rounded p-3 border border-emerald-900/30">{qa.best_answer}</p></div>}
                {qa.improvement_suggestions && <div><span className="text-xs text-yellow-400">💡 改进建议</span><p className="text-sm text-gray-300 mt-1">{qa.improvement_suggestions}</p></div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {report.knowledge_points.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><BookOpen className="w-5 h-5" /> 知识点卡片</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.knowledge_points.map((kp) => (
              <div key={kp.id} className="bg-gray-900 rounded-lg p-5 border border-gray-800">
                <h4 className="font-semibold text-emerald-400 mb-1">{kp.title}</h4>
                {kp.category && <span className="text-xs text-gray-500">{kp.category}</span>}
                <p className="text-sm text-gray-300 mt-2 mb-3 leading-relaxed">{kp.content.substring(0, 200)}{kp.content.length > 200 ? "..." : ""}</p>
                {kp.key_concepts.length > 0 && (
                  <div className="flex flex-wrap gap-1">{kp.key_concepts.map((c) => <span key={c} className="text-xs px-2 py-0.5 bg-gray-800 rounded text-gray-400">{c}</span>)}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {report.improvement_plan.length > 0 && (
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
          <h3 className="font-semibold mb-3 flex items-center gap-2"><Target className="w-4 h-4" /> 提升计划</h3>
          <div className="space-y-3">
            {report.improvement_plan.map((p, i) => (
              <div key={i} className="flex items-center gap-4">
                <span className="text-sm font-medium text-emerald-400 w-16">第{p.week}周</span>
                <span className="text-sm text-gray-300">{p.focus}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
