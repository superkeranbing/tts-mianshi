import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listRecordings, listResumes, uploadResume, analyzeInterview } from "../services/api";
import type { Recording, Resume } from "../types";
import { Brain, Upload, Loader2 } from "lucide-react";

export default function InterviewPage() {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selRec, setSelRec] = useState("");
  const [selRes, setSelRes] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    listRecordings().then(setRecordings).catch(() => {});
    listResumes().then(setResumes).catch(() => {});
  }, []);

  const handleAnalyze = async () => {
    if (!selRec) return;
    setLoading(true);
    try {
      const r = await analyzeInterview(selRec, selRes || undefined);
      navigate(`/report/${r.report_id}`);
    } catch (e) { alert(e instanceof Error ? e.message : "Analysis failed"); }
    setLoading(false);
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingResume(true);
    try {
      await uploadResume(file);
      setResumes(await listResumes());
    } catch (e) {
      alert(e instanceof Error ? e.message : "简历上传失败");
    } finally {
      setUploadingResume(false);
      e.target.value = "";
    }
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
              {recordings.map((r) => <option key={r.id} value={r.id}>{r.title}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">选择简历 <span className="text-gray-600">(可选)</span></label>
            <select value={selRes} onChange={(e) => setSelRes(e.target.value)} className="w-full px-4 py-2 bg-gray-800 rounded border border-gray-700 text-white text-sm">
              <option value="">-- 选择简历 --</option>
              {resumes.map((r) => <option key={r.id} value={r.id}>{r.file_name}</option>)}
            </select>
          </div>
        </div>
        <button onClick={handleAnalyze} disabled={loading || !selRec} className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-white font-medium transition-colors flex items-center justify-center gap-2">
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> 分析中...</> : <><Brain className="w-4 h-4" /> 开始面试分析</>}
        </button>
      </div>

      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <h3 className="font-semibold mb-3 text-emerald-400 flex items-center gap-2"><Upload className="w-4 h-4" /> 上传简历</h3>
        <p className="text-gray-500 text-sm mb-3">上传简历后，AI 将结合你的经历给出更个性化的分析。</p>
        <label className={`inline-flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700 text-sm cursor-pointer transition-colors ${uploadingResume ? 'opacity-50 cursor-not-allowed' : ''}`}>
          {uploadingResume ? <Loader2 className="w-4 h-4 animate-spin" /> : '📎'}
          {uploadingResume ? '上传中...' : '选择简历文件 (PDF/DOC/DOCX)'}
          <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeUpload} disabled={uploadingResume} className="hidden" />
        </label>
      </div>
    </div>
  );
}
