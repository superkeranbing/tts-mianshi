import type { Recording, Transcript, Resume, InterviewReport } from "../types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail);
  }
  return res.json();
}

// Auth
export function register(username: string, password: string) {
  return request<{ access_token: string; user: { id: string; username: string } }>(
    "/auth/register",
    { method: "POST", body: JSON.stringify({ username, password }) }
  );
}

export function login(username: string, password: string) {
  return request<{ access_token: string; user: { id: string; username: string } }>(
    "/auth/login",
    { method: "POST", body: JSON.stringify({ username, password }) }
  );
}

// Recordings
export function listRecordings() {
  return request<Recording[]>("/recordings");
}

export function getRecording(id: string) {
  return request<Recording & { transcripts: Transcript[] }>(`/recordings/${id}`);
}

export function uploadRecording(file: File, title: string) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("title", title);
  return fetch(BASE + "/recordings/upload", { method: "POST", body: fd }).then((r) => r.json());
}

export function triggerTranscribe(id: string) {
  return request<{ status: string; segments: number }>(`/asr/${id}/transcribe`, { method: "POST" });
}

export function deleteRecording(id: string) {
  return request<{ ok: boolean }>(`/recordings/${id}`, { method: "DELETE" });
}

// Resumes
export function listResumes() {
  return request<Resume[]>("/resumes");
}

export function uploadResume(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return fetch(BASE + "/resumes/upload", { method: "POST", body: fd }).then((r) => r.json());
}

// Interview
export function analyzeInterview(recordingId: string, resumeId?: string) {
  return request<{ report_id: string; status: string }>("/interview/analyze", {
    method: "POST",
    body: JSON.stringify({ recording_id: recordingId, resume_id: resumeId || null }),
  });
}

export function listReports() {
  return request<InterviewReport[]>("/interview/reports");
}

export function getReport(id: string) {
  return request<InterviewReport>(`/interview/reports/${id}`);
}

// Export
export function exportRecording(id: string, format: "txt" | "srt") {
  window.open(BASE + `/export/${id}/${format}`, "_blank");
}

export function updateTranscript(id: string, content: string, speakerName?: string) {
  const fd = new FormData();
  fd.append("content", content);
  if (speakerName) fd.append("speaker_name", speakerName);
  return fetch(BASE + `/recordings/transcripts/${id}`, { method: "PUT", body: fd }).then((r) => r.json());
}
