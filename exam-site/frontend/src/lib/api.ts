import axios from 'axios';
import type {
  ChatMessage,
  ChatResponse,
  ChatSource,
  ExamConfig,
  ExamQuestion,
  ExamResult,
  KnowledgeCard,
  Question,
  QuestionStats,
  TopicAnalysis,
  WeakPoint,
  StudyPlan,
  AgentInfo,
} from '../types';

export type {
  AgentInfo,
  ChatMessage,
  ChatResponse,
  ChatSource,
  ExamConfig,
  ExamQuestion,
  ExamResult,
  KnowledgeCard,
  Question,
  QuestionStats,
  StudyPlan,
  TopicAnalysis,
  WeakPoint,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
});

// ── Questions ──────────────────────────────────────────────────────────────

export async function getQuestionStats(): Promise<QuestionStats> {
  const { data } = await api.get('/questions/stats');
  return data;
}

export async function getQuestions(
  type?: string,
  offset = 0,
  limit = 50,
  keyword?: string,
): Promise<{ questions: Question[]; total: number; has_more: boolean }> {
  const params: Record<string, string | number> = { offset, limit };
  if (type) params.type = type;
  if (keyword) params.keyword = keyword;
  const { data } = await api.get('/questions', { params });
  return data;
}

export async function getQuestionById(id: number): Promise<Question> {
  const { data } = await api.get(`/questions/${id}`);
  return data;
}

export async function getQuestionsByType(
  qtype: string,
  offset = 0,
  limit = 50,
): Promise<{ questions: Question[]; total: number }> {
  const { data } = await api.get(`/questions/type/${qtype}`, {
    params: { offset, limit },
  });
  return data;
}

export async function searchQuestions(
  q: string,
  limit = 20,
): Promise<{ results: Question[]; total: number }> {
  const { data } = await api.get('/search', { params: { q, limit } });
  return data;
}

// ── Exam ───────────────────────────────────────────────────────────────────

export async function createExam(
  config?: Partial<ExamConfig>,
): Promise<{
  session_id: string;
  config: ExamConfig;
  questions: ExamQuestion[];
  total: number;
  started_at: string;
}> {
  const { data } = await api.post('/exam/create', config || {});
  return data;
}

export async function submitExamAnswer(
  sessionId: string,
  questionId: number,
  answer: string,
  timeSpentMs = 0,
): Promise<{ is_correct: boolean; correct_answer: string }> {
  const { data } = await api.post(`/exam/${sessionId}/answer`, {
    question_id: questionId,
    answer,
    time_spent_ms: timeSpentMs,
  });
  return data;
}

export async function completeExam(
  sessionId: string,
): Promise<ExamResult> {
  const { data } = await api.post(`/exam/${sessionId}/complete`);
  return data;
}

export async function getExamProgress(
  sessionId: string,
): Promise<{
  total: number;
  answered: number;
  remaining: number;
  current_correct: number;
  progress_percentage: number;
}> {
  const { data } = await api.get(`/exam/${sessionId}/progress`);
  return data;
}

export async function getExamResult(sessionId: string): Promise<ExamResult> {
  const { data } = await api.get(`/exam/${sessionId}/result`);
  return data;
}

export async function getExamWrongQuestions(sessionId: string) {
  const { data } = await api.get(`/exam/${sessionId}/wrong`);
  return data;
}

export async function deleteExamSession(sessionId: string) {
  const { data } = await api.delete(`/exam/${sessionId}`);
  return data;
}

// ── Practice ───────────────────────────────────────────────────────────────

export async function startPractice(
  mode: string,
  count = 20,
  types = ['single', 'multiple', 'truefalse'],
): Promise<{ questions: Question[]; total: number }> {
  const { data } = await api.post('/practice/start', {
    mode, count, types,
  });
  return data;
}

// ── AI Multi-Agent ─────────────────────────────────────────────────────────

export async function getAIAgents(): Promise<{ agents: AgentInfo[] }> {
  const { data } = await api.get('/ai/agents');
  return data;
}

export async function aiSummarize(
  mode = 'full_summary',
  questions?: Question[],
) {
  const body: Record<string, unknown> = { mode };
  if (questions) body.questions = questions;
  const { data } = await api.post('/ai/summarize', body);
  return data;
}

export async function aiExplain(
  question: Question,
  userAnswer: string,
): Promise<AIExplanationResponse> {
  const { data } = await api.post('/ai/explain', {
    question,
    user_answer: userAnswer,
  });
  return data;
}

export interface AIExplanationData {
  summary: string;
  reasoning: string;
  mistake_analysis: string;
  knowledge_points: string[];
  study_tip: string;
  correct_answer: string;
  source: 'openai' | 'local';
  fallback_reason?: string;
}

export interface AIExplanationResponse {
  agent: string;
  success: boolean;
  data: AIExplanationData;
  model: string | null;
  execution_time_ms: number;
}

export async function aiAnalyze(
  mode = 'full_analysis',
  examRecords: unknown[] = [],
) {
  const { data } = await api.post('/ai/analyze', {
    mode,
    exam_records: examRecords,
  });
  return data;
}

export async function aiPredict(
  mode = 'full_prediction',
  questions?: Question[],
) {
  const body: Record<string, unknown> = { mode };
  if (questions) body.questions = questions;
  const { data } = await api.post('/ai/predict', body);
  return data;
}

export async function aiPlan(
  planType = 'exam_prep',
  examDate?: string,
  dailyMinutes = 30,
  currentLevel = 'beginner',
) {
  const { data } = await api.post('/ai/plan', {
    plan_type: planType,
    exam_date: examDate,
    daily_minutes: dailyMinutes,
    current_level: currentLevel,
  });
  return data;
}

export async function aiFullAnalysis(body: {
  examRecords?: unknown[];
  questions?: Question[];
}) {
  const { data } = await api.post('/ai/full-analysis', body || {});
  return data;
}

export async function aiStudyMaterials() {
  const { data } = await api.post('/ai/study-materials');
  return data;
}

export async function aiExamHelp(
  question: Question,
  userAnswer: string,
) {
  const { data } = await api.post('/ai/exam-help', {
    question,
    user_answer: userAnswer,
  });
  return data;
}

// ── Knowledge ──────────────────────────────────────────────────────────────

export async function getKnowledgeCards(typeFilter?: string) {
  const { data } = await api.get('/knowledge/cards', {
    params: typeFilter ? { type_filter: typeFilter } : {},
  });
  return data;
}

export async function getKnowledgeMap() {
  const { data } = await api.get('/knowledge/map');
  return data;
}

// ── Quiz ───────────────────────────────────────────────────────────────────

export async function createRandomQuiz(
  count = 20,
  types = ['single', 'multiple', 'truefalse'],
) {
  const { data } = await api.post('/quiz/random', { count, types });
  return data;
}

export async function gradeQuiz(quizId: string, answers: Record<string, string>) {
  const { data } = await api.post(`/quiz/${quizId}/grade`, { answers });
  return data;
}

// ── Analytics ──────────────────────────────────────────────────────────────

export async function getAnalyticsDashboard(examRecords: unknown[] = []) {
  const { data } = await api.post('/analytics/dashboard', {
    exam_records: examRecords,
  });
  return data;
}

// ── RAG Chat ───────────────────────────────────────────────────────────────

export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
): Promise<ChatResponse> {
  const { data } = await api.post('/chat', { message, history });
  return data;
}

export async function getChatSources() {
  const { data } = await api.get('/chat/sources');
  return data;
}
