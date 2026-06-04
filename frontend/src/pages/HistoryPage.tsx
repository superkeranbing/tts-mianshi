import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listRecordings } from "../services/api";
import type { Recording } from "../types";
import { History } from "lucide-react";

export default function HistoryPage() {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const navigate = useNavigate();

  useEffect(() => { listRecordings().then(setRecordings).catch(() => {}); }, []);

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
    </div>
  );
}
