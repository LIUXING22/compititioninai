export interface Question {
  id: number;
  type: 'single' | 'multiple' | 'truefalse';
  question: string;
  options: Record<string, string>;
  answer: string;
}

export interface ExamConfig {
  total_questions?: number;
  time_limit_minutes: number;
  single_score?: number;
  multiple_score?: number;
  truefalse_score?: number;
  multiple_penalty?: number;
}

export interface ExamSession {
  session_id: string;
  config: ExamConfig;
  questions: ExamQuestion[];
  started_at: string;
  total: number;
}

export interface ExamQuestion {
  order: number;
  id: number;
  type: Question['type'];
  question: string;
  options: Record<string, string>;
}

export interface ExamResult {
  session_id: string;
  completed: boolean;
  score: {
    raw: number;
    max: number;
    percentage: number;
    grade: string;
  };
  summary: {
    total: number;
    correct: number;
    incorrect: number;
    time_seconds: number;
  };
  by_type: Record<string, { total: number; correct: number; rate: number }>;
  questions: ExamResultQuestion[];
}

export interface ExamResultQuestion {
  id: number;
  order: number;
  type: Question['type'];
  question: string;
  options: Record<string, string>;
  user_answer?: string;
  correct_answer: string;
  is_correct: boolean;
  time_spent_ms: number;
}

export interface QuestionStats {
  total: number;
  single: number;
  multiple: number;
  truefalse: number;
  by_type: Record<string, { total: number; correct: number; rate: number }>;
}

export interface KnowledgeCard {
  id: number;
  front: string;
  back: string;
  type: string;
}

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
  capabilities: string[];
}

export interface TopicAnalysis {
  name: string;
  stats: { total: number; single: number; multiple: number; tf: number };
  percentage: number;
  key_concepts: string[];
  difficulty: string;
}

export interface WeakPoint {
  id: number;
  question: string;
  type: string;
  wrong_count: number;
  priority: string;
}

export interface StudyPlanDay {
  day: number;
  phase: string;
  focus: string;
  target_questions: number;
  estimated_minutes: number;
  study_tips: string;
}

export interface StudyPlan {
  days_left: number;
  daily_minutes: number;
  total_hours: number;
  phases: { name: string; phase: string; focus: string; questions: number }[];
  daily_plans: StudyPlanDay[];
  milestones: { day: number; milestone: string; checkpoint: string }[];
}

// Chat RAG types
export interface ChatSource {
  chunk_id: string;
  source: string;
  relevance: number;
  excerpt: string;
  question_id?: number;
  question_type?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  timestamp?: string;
}

export interface ChatResponse {
  reply: string;
  sources: ChatSource[];
  context_used: boolean;
  model: string | null;
  execution_time_ms: number;
  error?: string;
}
