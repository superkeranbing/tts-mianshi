import { useState, useRef, useCallback, useEffect } from "react";

export interface StreamResult {
  type: "partial_result" | "final_result" | "error";
  text: string;
  speaker?: string;
  is_final?: boolean;
  start_time?: number;
  end_time?: number;
  timestamp?: number;
  message?: string;
}

export interface AudioRecorderState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  streamResults: StreamResult[];
  error: string | null;
}

export function useAudioRecorder() {
  const [state, setState] = useState<AudioRecorderState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
    streamResults: [],
    error: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const getWsUrl = () => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws/asr/stream`;
  };

  const startRecording = useCallback(async () => {
    setState((s) => ({ ...s, error: null, streamResults: [] }));

    try {
      // Get microphone stream
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Connect WebSocket
      const wsUrl = getWsUrl();
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        // Start MediaRecorder
        const recorder = new MediaRecorder(stream, {
          mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
            ? "audio/webm;codecs=opus"
            : "audio/webm",
        });
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = (event) => {
          if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
            ws.send(event.data);
          }
        };

        recorder.start(250); // Send chunks every 250ms
        setState((s) => ({ ...s, isRecording: true, isPaused: false, duration: 0 }));

        // Start duration timer
        const startTime = Date.now();
        timerRef.current = window.setInterval(() => {
          setState((s) => ({ ...s, duration: (Date.now() - startTime) / 1000 }));
        }, 100);
      };

      ws.onmessage = (event) => {
        try {
          const result: StreamResult = JSON.parse(event.data);
          setState((s) => ({ ...s, streamResults: [...s.streamResults, result] }));
        } catch {}
      };

      ws.onerror = () => {
        setState((s) => ({ ...s, error: "WebSocket connection error" }));
      };

      ws.onclose = () => {};
    } catch (err) {
      const msg = err instanceof DOMException && err.name === "NotAllowedError"
        ? "Microphone access denied. Please allow microphone permissions."
        : err instanceof Error ? err.message : "Failed to start recording";
      setState((s) => ({ ...s, error: msg }));
    }
  }, []);

  const stopRecording = useCallback(() => {
    // Stop MediaRecorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }

    // Stop timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Stop media tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    setState((s) => ({ ...s, isRecording: false, isPaused: false }));
  }, []);

  const togglePause = useCallback(() => {
    if (!mediaRecorderRef.current) return;
    if (mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.pause();
      setState((s) => ({ ...s, isPaused: true }));
    } else if (mediaRecorderRef.current.state === "paused") {
      mediaRecorderRef.current.resume();
      setState((s) => ({ ...s, isPaused: false }));
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (wsRef.current) wsRef.current.close();
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
  }, []);

  return {
    ...state,
    startRecording,
    stopRecording,
    togglePause,
  };
}