import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getRecording, analyzeInterview, exportRecording } from "../services/api";
import type { Recording, Transcript } from "../types";
import { ArrowLeft, Download, Brain, Loader2 } from "lucide-react";

function fmtTime(s: number) {
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export default function RecordingPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [rec, setRec] = useState<Recording | null>(null);
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (!id) return;
    getRecording(id).then((r) => { setRec(r); setTranscripts(r.transcripts || []); }).catch(() => navigate("/"));
  }, [id, navigate]);

  const handleAnalyze = async () => {
    if (!id) return;
    setAnalyzing(true);
    try {
      const r = await analyzeInterview(id);
      navigate(`/report/${r.report_id}`);
    } catch (e) { alert(e instanceof Error ? e.message : "Analysis failed"); }
    setAnalyzing(false);
  };

  if (!rec) return <div className="p-12 text-center text-gray-500">加载中...</div>;

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate("/")} className="text-gray-500 hover:text-gray-300 transition-colors"><ArrowLeft className="w-5 h-5" /></button>
        <h2 className="text-xl font-bold">{rec.title}</h2>
        <span className={`text-xs px-2 py-1 rounded ${rec.status === "completed" ? "bg-emerald-900/50 text-emerald-400" : "bg-yellow-900/50 text-yellow-400"}`}>
          {rec.status === "completed" ? "已完成" : "处理中"}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: "音频时长", value: rec.audio_duration ? `${Math.floor(rec.audio_duration)}秒` : "--" },
          { label: "转写段落", value: transcripts.length },
          { label: "说话人数", value: new Set(transcripts.map((t) => t.speaker)).size },
        ].map((s) => (
          <div key={s.label} className="bg-gray-900 rounded-lg p-4 border border-gray-800 text-center">
            <p className="text-2xl font-bold text-emerald-400">{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="flex gap-3 mb-6">
        <button onClick={handleAnalyze} disabled={analyzing} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-sm transition-colors flex items-center gap-2">
          {analyzing ? <><Loader2 className="w-4 h-4 animate-spin" /> 分析中...</> : <><Brain className="w-4 h-4" /> 面试分析</>}
        </button>
        <button onClick={() => id && exportRecording(id, "txt")} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors flex items-center gap-2">
          <Download className="w-4 h-4" /> TXT
        </button>
        <button onClick={() => id && exportRecording(id, "srt")} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors flex items-center gap-2">
          <Download className="w-4 h-4" /> SRT
        </button>
      </div>

      <div className="bg-gray-900 rounded-lg border border-gray-800">
        <div className="px-6 py-4 border-b border-gray-800 font-semibold">📝 转写文本</div>
        <div className="divide-y divide-gray-800">
          {transcripts.map((t) => (
            <div key={t.id} className="px-6 py-4 flex gap-4">
              <div className="flex-shrink-0">
                <span className={`inline-flex w-8 h-8 rounded-full items-center justify-center text-xs font-medium ${t.speaker === "面试官" ? "bg-blue-900/50 text-blue-400" : "bg-emerald-900/50 text-emerald-400"}`}>
                  {(t.speaker_name || t.speaker)[0]}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-sm">{t.speaker_name || t.speaker}</span>
                  <span className="text-xs text-gray-600">{fmtTime(t.start_time)}</span>
                  <span className="text-xs px-1.5 py-0.5 bg-gray-800 rounded text-gray-500">{t.speaker}</span>
                </div>
                <p className="text-sm text-gray-300 leading-relaxed break-words">{t.content}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
