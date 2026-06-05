// ====== Type Definitions ======

export interface User {
  id: string;
  username: string;
  email?: string;
  created_at: string;
}

export interface Recording {
  id: string;
  title: string;
  audio_duration?: number;
  audio_format?: string;
  status: string;
  language: string;
  created_at: string;
  transcripts?: Transcript[];
}

export interface Transcript {
  id: string;
  speaker: string;
  speaker_name?: string;
  content: string;
  start_time: number;
  end_time: number;
  confidence: number;
}

export interface Resume {
  id: string;
  file_name: string;
  file_type: string;
  parsed_data: Record<string, unknown>;
  raw_text?: string;
  created_at: string;
}

export interface QAPair {
  id: string;
  question: string;
  question_category?: string;
  your_answer?: string;
  best_answer?: string;
  answer_score?: number;
  improvement_suggestions?: string;
}

export interface KnowledgePoint {
  id: string;
  title: string;
  category?: string;
  key_concepts: string[];
  content: string;
  resources: { title: string; url: string }[];
  interview_tips: string[];
}

export interface InterviewReport {
  id: string;
  recording_id: string;
  resume_id?: string;
  overall_score?: number;
  strengths: string[];
  weaknesses: string[];
  improvement_plan: { week: number; focus: string }[];
  summary?: string;
  qa_pairs: QAPair[];
  knowledge_points: KnowledgePoint[];
  created_at: string;
}

export interface ApiError {
  detail: string;
}

// Conversation summary (lightweight, no interview analysis)
export interface ConversationSummary {
  summary: string;
  topics: string[];
  key_points: string[];
}

export interface SimpleQAPair {
  question: string;
  answer: string;
}

export interface ConversationQA {
  qa_pairs: SimpleQAPair[];
}
