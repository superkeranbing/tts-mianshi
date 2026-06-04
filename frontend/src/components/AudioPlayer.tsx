import { useEffect, useRef, useState, useCallback, forwardRef, useImperativeHandle } from "react";
import WaveSurfer from "wavesurfer.js";
import { Play, Pause, SkipBack, SkipForward, Volume2 } from "lucide-react";

export interface AudioPlayerHandle {
  seekTo: (time: number) => void;
  getCurrentTime: () => number;
  play: () => void;
  pause: () => void;
}

interface Props {
  audioUrl: string;
  onTimeUpdate?: (time: number) => void;
  onReady?: (duration: number) => void;
  markers?: { time: number; label: string; color: string }[];
}

const AudioPlayer = forwardRef<AudioPlayerHandle, Props>(
  ({ audioUrl, onTimeUpdate, onReady, markers }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WaveSurfer | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(0.7);

    useEffect(() => {
      if (!containerRef.current) return;
      const ws = WaveSurfer.create({
        container: containerRef.current,
        waveColor: "#374151",
        progressColor: "#10b981",
        cursorColor: "#10b981",
        barWidth: 2,
        barGap: 1,
        barRadius: 2,
        height: 80,
        url: audioUrl,
        backend: "WebAudio",
      });

      ws.on("ready", () => {
        setDuration(ws.getDuration());
        onReady?.(ws.getDuration());
        // Draw markers
        markers?.forEach((m) => {
          const pct = m.time / ws.getDuration();
          const markerEl = document.createElement("div");
          markerEl.style.cssText = `position:absolute;left:${pct * 100}%;top:0;width:2px;height:100%;background:${m.color};z-index:10;cursor:pointer;`;
          markerEl.title = m.label;
          containerRef.current?.appendChild(markerEl);
        });
      });
      ws.on("play", () => setIsPlaying(true));
      ws.on("pause", () => setIsPlaying(false));
      ws.on("timeupdate", (t) => {
        setCurrentTime(t);
        onTimeUpdate?.(t);
      });
      ws.on("finish", () => setIsPlaying(false));
      ws.setVolume(volume);
      wsRef.current = ws;

      return () => { ws.destroy(); };
    }, [audioUrl]);

    useEffect(() => { wsRef.current?.setVolume(volume); }, [volume]);

    useImperativeHandle(ref, () => ({
      seekTo: (time: number) => wsRef.current?.seekTo(time / (wsRef.current.getDuration() || 1)),
      getCurrentTime: () => wsRef.current?.getCurrentTime() ?? 0,
      play: () => wsRef.current?.play(),
      pause: () => wsRef.current?.pause(),
    }));

    const togglePlay = () => { isPlaying ? wsRef.current?.pause() : wsRef.current?.play(); };
    const skip = (s: number) => wsRef.current?.seekTo(Math.min(1, Math.max(0, (currentTime + s) / (duration || 1))));
    const fmt = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

    return (
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <div ref={containerRef} className="w-full rounded overflow-hidden" />
        <div className="flex items-center gap-3 mt-3">
          <button onClick={() => skip(-10)} className="text-gray-400 hover:text-gray-200 transition-colors"><SkipBack className="w-4 h-4" /></button>
          <button onClick={togglePlay} className="w-10 h-10 rounded-full bg-emerald-600 hover:bg-emerald-500 flex items-center justify-center transition-colors">
            {isPlaying ? <Pause className="w-4 h-4 text-white" /> : <Play className="w-4 h-4 text-white ml-0.5" />}
          </button>
          <button onClick={() => skip(10)} className="text-gray-400 hover:text-gray-200 transition-colors"><SkipForward className="w-4 h-4" /></button>
          <span className="text-xs text-gray-400 font-mono w-24 text-center">{fmt(currentTime)} / {fmt(duration)}</span>
          <div className="flex-1" />
          <Volume2 className="w-4 h-4 text-gray-500" />
          <input type="range" min="0" max="1" step="0.05" value={volume} onChange={(e) => setVolume(+e.target.value)} className="w-20 h-1 accent-emerald-500" />
        </div>
      </div>
    );
  }
);

AudioPlayer.displayName = "AudioPlayer";
export default AudioPlayer;
