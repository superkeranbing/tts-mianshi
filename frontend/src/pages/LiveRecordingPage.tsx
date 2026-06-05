import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { Mic, Square, Pause, Play, Loader2, ArrowLeft, Upload } from "lucide-react";

function fmtTime(s: number) {
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export default function LiveRecordingPage() {
  const navigate = useNavigate();
  const { isRecording, isPaused, duration, streamResults, error, startRecording, stopRecording, togglePause } = useAudioRecorder();
  const [title, setTitle] = useState("");
  const [uploaded, setUploaded] = useState(false);
  const resultsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    resultsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [streamResults]);

  const handleStartStop = async () => {
    if (!isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  };

  const finalResults = streamResults.filter((r) => r.type === "partial_result" || r.type === "final_result");

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate("/")} className="text-gray-500 hover:text-gray-300 transition-colors"><ArrowLeft className="w-5 h-5" /></button>
        <h2 className="text-xl font-bold">实时录音</h2>
      </div>

      {/* Recording Controls */}
      <div className="bg-gray-900 rounded-lg p-8 border border-gray-800 text-center mb-6">
        {/* Timer */}
        <p className="text-4xl font-mono font-bold mb-4 text-emerald-400">{fmtTime(duration)}</p>

        {/* Controls */}
        <div className="flex items-center justify-center gap-4 mb-4">
          <button
            onClick={togglePause}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
              isRecording && !isPaused ? "bg-yellow-600 hover:bg-yellow-500" : "bg-gray-700 text-gray-400"
            }`}
            disabled={!isRecording}
          >
            {isPaused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
          </button>

          <button
            onClick={handleStartStop}
            className={`w-16 h-16 rounded-full flex items-center justify-center transition-colors ${
              isRecording ? "bg-red-600 hover:bg-red-500 animate-pulse" : "bg-emerald-600 hover:bg-emerald-500"
            }`}
          >
            {isRecording ? <Square className="w-6 h-6 text-white" /> : <Mic className="w-6 h-6 text-white" />}
          </button>
        </div>

        <p className="text-sm text-gray-500">
          {isRecording ? (isPaused ? "已暂停" : "录音中...") : "准备录音"}
        </p>

        {/* Title Input */}
        <div className="mt-4 flex items-center justify-center gap-2">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="输入录音标题（可选）"
            className="px-4 py-2 bg-gray-800 rounded border border-gray-700 text-white text-sm w-64 outline-none focus:border-emerald-500 transition-colors"
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-lg p-4 mb-6">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Live Transcription */}
      {finalResults.length > 0 && (
        <div className="bg-gray-900 rounded-lg border border-gray-800">
          <div className="px-6 py-3 border-b border-gray-800 font-semibold text-sm">
            实时转写
          </div>
          <div className="divide-y divide-gray-800 max-h-[40vh] overflow-y-auto">
            {finalResults.map((r, i) => (
              <div key={i} className="px-6 py-3 flex gap-3">
                <span className="text-xs text-gray-500 mt-0.5 font-mono w-12 flex-shrink-0">
                  {r.timestamp ? fmtTime(r.timestamp) : "--"}
                </span>
                <div className="flex-1">
                  <p className="text-sm text-gray-300">{r.text}</p>
                </div>
              </div>
            ))}
            <div ref={resultsEndRef} />
          </div>
        </div>
      )}

      {/* Recording not started */}
      {finalResults.length === 0 && !error && (
        <div className="bg-gray-900 rounded-lg p-12 border border-gray-800 text-center">
          <Mic className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <p className="text-gray-500">点击麦克风开始实时录音</p>
          <p className="text-gray-600 text-xs mt-2">录音成功后自动保存并开始转写</p>
        </div>
      )}
    </div>
  );
}

