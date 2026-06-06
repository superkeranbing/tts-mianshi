import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listRecordings, listReports, listResumes } from "../services/api";
import type { Recording, InterviewReport, Resume } from "../types";
import { History, FileText } from "lucide-react";

export default function HistoryPage() {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [reports, setReports] = useState<InterviewReport[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    listRecordings().then(setRecordings).catch(() => {});
    listReports().then(setReports).catch(() => {});
    listResumes().then(setResumes).catch(() => {});
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h2 className="text-xl font-bold mb-6 flex items-center gap-2"><History className="w-5 h-5" /> 历史记录</h2>
      {recordings.length === 0 ? (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-12 text-center text-gray-500">
          <p className="text-4xl mb-3">📭</p><p>暂无历史记录</p>
        </div>
      ) : (
        <div className="bg-gray-900 rounded-lg border border-gray-800 divide-y divide-gray-800">
          {recordings.map((r) => (
            <div key={r.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-800/50 cursor-pointer transition-colors" onClick={() => navigate(`/recording/${r.id}`)}>
              <div>
                <p className="font-medium">{r.title}</p>
                <p className="text-sm text-gray-500">{new Date(r.created_at).toLocaleString("zh-CN")} · {r.audio_format?.toUpperCase()}</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded ${r.status === "completed" ? "bg-emerald-900/50 text-emerald-400" : "bg-yellow-900/50 text-yellow-400"}`}>
                {r.status === "completed" ? "已完成" : "处理中"}
              </span>
            </div>
          ))}
        </div>
      )}

      {reports.length > 0 && (
        <>
          <h2 className="text-xl font-bold mb-6 mt-10 flex items-center gap-2"><FileText className="w-5 h-5" /> 面试分析报告</h2>
          <div className="bg-gray-900 rounded-lg border border-gray-800 divide-y divide-gray-800">
            {reports.map((r) => {
              const rec = recordings.find((x) => x.id === r.recording_id);
              const res = resumes.find((x) => x.id === r.resume_id);
              return (
                <div key={r.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-800/50 cursor-pointer transition-colors" onClick={() => navigate("/report/" + r.id)}>
                  <div>
                    <p className="font-medium">{rec?.title || "未知录音"}</p>
                    <p className="text-sm text-gray-500">
                      简历: {res?.file_name || "空"} | 评分: {r.overall_score ?? "--"} | {new Date(r.created_at).toLocaleString("zh-CN")}
                    </p>
                  </div>
                  <span className={"text-xs px-2 py-1 rounded " + (r.status === "completed" ? "bg-emerald-900/50 text-emerald-400" : r.status === "failed" ? "bg-red-900/50 text-red-400" : "bg-yellow-900/50 text-yellow-400")}>
                    {r.status === "completed" ? "已完成" : r.status === "failed" ? "失败" : "处理中"}
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
