import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listRecordings, listResumes, uploadResume, analyzeInterview, getReport, deleteResume } from "../services/api";
import type { Recording, Resume } from "../types";
import { Brain, Upload, Loader2, Trash2 } from "lucide-react";

export default function InterviewPage() {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selRec, setSelRec] = useState("");
  const [selRes, setSelRes] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const navigate = useNavigate();

  const loadResumes = async () => {
    try { setResumes(await listResumes()); } catch {}
  };

  useEffect(() => {
    listRecordings().then(setRecordings).catch(() => {});
    loadResumes();
  }, []);

  const handleAnalyze = async () => {
    if (!selRec) return;
    setLoading(true);
    try {
      const r = await analyzeInterview(selRec, selRes || undefined);
      const reportId = r.report_id;
      const poll = async (): Promise<void> => {
        const report = await getReport(reportId);
        if (report.status === "completed") {
          navigate("/report/" + reportId);
        } else if (report.status === "failed") {
          alert("分析失败，请重试");
          setLoading(false);
        } else {
          setTimeout(() => poll(), 2000);
        }
      };
      await poll();
    } catch (e) {
      alert(e instanceof Error ? e.message : "分析失败");
      setLoading(false);
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingResume(true);
    try {
      await uploadResume(file);
      await loadResumes();
    } catch (e) {
      alert(e instanceof Error ? e.message : "上传失败");
    } finally {
      setUploadingResume(false);
      e.target.value = "";
    }
  };

  const handleDeleteResume = async (id: string) => {
    try {
      await deleteResume(id);
      if (selRes === id) setSelRes("");
      await loadResumes();
    } catch {}
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h2 className="text-xl font-bold mb-6 flex items-center gap-2"><Brain className="w-5 h-5" /> 面试分析</h2>
      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">选择录音</label>
            <select value={selRec} onChange={(e) => setSelRec(e.target.value)} className="w-full px-4 py-2 bg-gray-800 rounded border border-gray-700 text-white text-sm">
              <option value="">-- 选择面试录音 --</option>
              {recordings.filter(r => r.status === "completed").map((r) => <option key={r.id} value={r.id}>{r.title}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">选择简历 <span className="text-gray-600">(可选)</span></label>
            <select value={selRes} onChange={(e) => setSelRes(e.target.value)} className="w-full px-4 py-2 bg-gray-800 rounded border border-gray-700 text-white text-sm">
              <option value="">-- 不选择简历 --</option>
              {resumes.map((r) => <option key={r.id} value={r.id}>{r.file_name}</option>)}
            </select>
          </div>
        </div>
        <button onClick={handleAnalyze} disabled={loading || !selRec} className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-white font-medium transition-colors flex items-center justify-center gap-2">
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> 分析中...</> : <><Brain className="w-4 h-4" /> 开始面试分析</>}
        </button>
      </div>
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <h3 className="font-semibold mb-4 text-emerald-400 flex items-center gap-2"><Upload className="w-4 h-4" /> 简历管理</h3>
        {resumes.length > 0 && (
          <div className="mb-4 divide-y divide-gray-800 border border-gray-800 rounded-lg overflow-hidden">
            {resumes.map((r) => (
              <div key={r.id} className="px-4 py-3 flex items-center justify-between bg-gray-800/50">
                <div>
                  <p className="text-sm font-medium">{r.file_name}</p>
                  <p className="text-xs text-gray-500">{new Date(r.created_at).toLocaleString("zh-CN")} . {r.file_type?.toUpperCase()}</p>
                </div>
                <button onClick={() => handleDeleteResume(r.id)} className="text-gray-600 hover:text-red-400 transition-colors p-1">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
        <p className="text-gray-500 text-sm mb-3">{resumes.length === 0 ? "还没有简历，点击下方上传" : "继续上传新简历"}</p>
        <label className={"inline-flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700 text-sm cursor-pointer transition-colors " + (uploadingResume ? "opacity-50 cursor-not-allowed" : "")}>
          {uploadingResume ? <Loader2 className="w-4 h-4 animate-spin" /> : "+"}
          {uploadingResume ? "上传中..." : "选择简历文件"}
          <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeUpload} disabled={uploadingResume} className="hidden" />
        </label>
      </div>
    </div>
  );
}
