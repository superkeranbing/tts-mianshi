import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { listRecordings, uploadRecording, triggerTranscribe, deleteRecording } from "../services/api";
import type { Recording } from "../types";
import { Upload, Mic, FileText, Trash2, Loader2 } from "lucide-react";

export default function HomePage() {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [title, setTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    try { setRecordings(await listRecordings()); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const data = await uploadRecording(file, title || file.name);
      await triggerTranscribe(data.id);
      setTitle("");
      if (fileRef.current) fileRef.current.value = "";
      load();
    } catch (err) { alert(err instanceof Error ? err.message : "Upload failed"); }
    setUploading(false);
  };

  const handleDelete = async (id: string) => {
    try { await deleteRecording(id); load(); } catch {}
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
        {/* Upload */}
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-emerald-400">
            <Upload className="w-5 h-5" /> 上传面试录音
          </h3>
          <form onSubmit={handleUpload} className="space-y-3">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="录音标题（如：腾讯前端一面）"
              className="w-full px-4 py-2 bg-gray-800 rounded border border-gray-700 text-white outline-none text-sm focus:border-emerald-500 transition-colors"
            />
            <div
              onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center cursor-pointer hover:border-emerald-500 transition-colors"
            >
              <input ref={fileRef} type="file" accept="audio/*" className="hidden" onChange={() => setTitle((f) => f || fileRef.current?.files?.[0]?.name || "")} />
              <Mic className="w-8 h-8 mx-auto mb-2 text-gray-500" />
              <p className="text-gray-400 text-sm">点击选择音频文件</p>
              <p className="text-gray-600 text-xs mt-1">支持 MP3 / WAV / M4A</p>
            </div>
            <button
              type="submit"
              disabled={uploading}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              {uploading ? <><Loader2 className="w-4 h-4 animate-spin" /> 上传中...</> : "上传并开始转写"}
            </button>
          </form>
        </div>

        {/* Quick Actions */}
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 flex flex-col justify-center gap-4">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2 text-emerald-400">
            <FileText className="w-5 h-5" /> 快速操作
          </h3>
          <p className="text-gray-400 text-sm">上传简历和录音后，AI 自动分析面试表现，生成提升报告。</p>
          <button
            onClick={() => navigate("/interview")}
            className="w-full py-2.5 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700 text-sm transition-colors"
          >
            🎯 创建分析
          </button>
          <button
            onClick={() => navigate("/history")}
            className="w-full py-2.5 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700 text-sm transition-colors"
          >
            📋 查看历史
          </button>
        </div>
      </div>

      {/* Recording List */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
          <h3 className="font-semibold">📂 录音列表 <span className="text-gray-500 text-sm ml-2">{recordings.length} 条记录</span></h3>
        </div>
        {recordings.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <p className="text-4xl mb-3">🎙</p>
            <p>暂无录音，上传一个面试录音开始吧</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {recordings.map((r) => (
              <div
                key={r.id}
                className="px-6 py-4 flex items-center justify-between hover:bg-gray-800/50 transition-colors cursor-pointer"
                onClick={() => navigate(`/recording/${r.id}`)}
              >
                <div>
                  <p className="font-medium">{r.title}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(r.created_at).toLocaleString("zh-CN")}
                    {r.audio_duration ? ` · ${Math.floor(r.audio_duration)}秒` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-1 rounded ${r.status === "completed" ? "bg-emerald-900/50 text-emerald-400" : "bg-yellow-900/50 text-yellow-400"}`}>
                    {r.status === "completed" ? "已完成" : "处理中"}
                  </span>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(r.id); }}
                    className="text-gray-600 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
