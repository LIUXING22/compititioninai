import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Play,
  RotateCcw,
  Trophy,
  ArrowRight,
  BookOpen,
  Loader2,
  PenLine,
  Sparkles,
} from 'lucide-react'
import {
  createExam,
  submitExamAnswer,
  completeExam,
  getExamProgress,
  getExamResult,
  type ExamQuestion,
  type ExamResult,
} from '../lib/api'
import WrongAnswerExplanation from '../components/WrongAnswerExplanation'

type ExamPhase = 'setup' | 'active' | 'result'
type AnswerResult = { is_correct: boolean; correct_answer: string }

export default function Exam() {
  const navigate = useNavigate()
  const [phase, setPhase] = useState<ExamPhase>('setup')
  const [sessionId, setSessionId] = useState('')
  const [questions, setQuestions] = useState<ExamQuestion[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [draftAnswers, setDraftAnswers] = useState<Record<number, string>>({})
  const [answerResults, setAnswerResults] = useState<Record<number, AnswerResult>>({})
  const [timeLeft, setTimeLeft] = useState(3600)
  const [result, setResult] = useState<ExamResult | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [answerSubmitting, setAnswerSubmitting] = useState(false)
  const [showAnswer, setShowAnswer] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval>>()

  const current = questions[currentIdx]
  const total = questions.length

  // Timer
  useEffect(() => {
    if (phase !== 'active') {
      if (timerRef.current) clearInterval(timerRef.current)
      return
    }
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          handleFinish()
          return 0
        }
        return t - 1
      })
    }, 1000)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [phase])

  const handleStart = useCallback(async () => {
    setSubmitting(true)
    try {
      const res = await createExam({
        total_questions: 50,
        time_limit_minutes: 60,
      })
      setSessionId(res.session_id)
      setQuestions(res.questions)
      setAnswers({})
      setDraftAnswers({})
      setAnswerResults({})
      setTimeLeft(60 * 60)
      setPhase('active')
    } finally {
      setSubmitting(false)
    }
  }, [])

  const handleAnswer = useCallback(async (answer: string) => {
    if (!current || phase !== 'active') return

    if (current.type === 'multiple') {
      setDraftAnswers((prev) => {
        const selected = new Set((prev[current.id] || '').split('').filter(Boolean))
        selected.has(answer) ? selected.delete(answer) : selected.add(answer)
        return { ...prev, [current.id]: [...selected].sort().join('') }
      })
      return
    }

    setAnswers((prev) => ({ ...prev, [current.id]: answer }))
    setAnswerSubmitting(true)
    try {
      const result = await submitExamAnswer(sessionId, current.id, answer)
      setAnswerResults((prev) => ({ ...prev, [current.id]: result }))
      setShowAnswer(true)
    } finally {
      setAnswerSubmitting(false)
    }
  }, [current, sessionId, phase])

  const submitMultipleAnswer = useCallback(async () => {
    if (!current || current.type !== 'multiple') return
    const answer = draftAnswers[current.id]
    if (!answer) return

    setAnswers((prev) => ({ ...prev, [current.id]: answer }))
    setAnswerSubmitting(true)
    try {
      const result = await submitExamAnswer(sessionId, current.id, answer)
      setAnswerResults((prev) => ({ ...prev, [current.id]: result }))
      setShowAnswer(true)
    } finally {
      setAnswerSubmitting(false)
    }
  }, [current, draftAnswers, sessionId])

  const handleNext = useCallback(() => {
    if (currentIdx < total - 1) {
      const nextIndex = currentIdx + 1
      setCurrentIdx(nextIndex)
      setShowAnswer(Boolean(answerResults[questions[nextIndex].id]))
    }
  }, [answerResults, currentIdx, questions, total])

  const handlePrev = useCallback(() => {
    if (currentIdx > 0) {
      const previousIndex = currentIdx - 1
      setCurrentIdx(previousIndex)
      setShowAnswer(Boolean(answerResults[questions[previousIndex].id]))
    }
  }, [answerResults, currentIdx, questions])

  const handleFinish = useCallback(async () => {
    if (!sessionId) return
    setSubmitting(true)
    try {
      const res = await completeExam(sessionId)
      setResult(res)
      setPhase('result')
    } finally {
      setSubmitting(false)
    }
  }, [sessionId])

  const handleRestart = useCallback(() => {
    setPhase('setup')
    setQuestions([])
    setAnswers({})
    setDraftAnswers({})
    setAnswerResults({})
    setCurrentIdx(0)
    setResult(null)
    setShowAnswer(false)
  }, [])

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const isTimeWarning = timeLeft < 300
  const answered = Object.keys(answers).length

  // ── Setup Phase ──────────────────────────────────────────────────────────
  if (phase === 'setup') {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-600 to-ai-500 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-primary-200">
            <PenLine className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mb-2">模拟考试</h1>
          <p className="text-slate-500">仿真考试环境，全面检验你的学习成果</p>
        </div>

        <div className="card p-6 space-y-5">
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: '题目数量', value: '50题' },
              { label: '考试时间', value: '60分钟' },
              { label: '单选题', value: '30题 × 1分' },
              { label: '多选题', value: '8题 × 2分' },
              { label: '判断题', value: '12题 × 1分' },
              { label: '总分', value: '66分' },
            ].map((item) => (
              <div key={item.label} className="bg-slate-50 rounded-xl p-3">
                <div className="text-xs text-slate-400 mb-1">{item.label}</div>
                <div className="font-semibold text-slate-700">{item.value}</div>
              </div>
            ))}
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <div className="flex gap-2">
              <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-medium mb-1">考试说明</p>
                <ul className="list-disc list-inside space-y-0.5 text-amber-700">
                  <li>考试全程60分钟，自动倒计时</li>
                  <li>多选题漏选得部分分，错选不扣分</li>
                  <li>完成后立即出分和详细解析</li>
                  <li>不可中途退出后重新进入</li>
                </ul>
              </div>
            </div>
          </div>

          <button
            className="btn-primary w-full py-3 text-lg"
            onClick={handleStart}
            disabled={submitting}
          >
            {submitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                准备题目中...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                开始考试
              </>
            )}
          </button>
        </div>
      </div>
    )
  }

  // ── Active Phase ─────────────────────────────────────────────────────────
  if (phase === 'active' && current) {
    const isAnswered = answers[current.id] !== undefined
    const userAnswer = answers[current.id]
    const selectedAnswer = current.type === 'multiple' && !showAnswer
      ? (draftAnswers[current.id] || '')
      : (userAnswer || '')
    const currentResult = answerResults[current.id]
    const isCorrect = currentResult?.is_correct ?? false

    return (
      <div className="max-w-5xl mx-auto">
        {/* Top bar */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-slate-500">
              {currentIdx + 1} / {total}
            </span>
            <div className="w-48 h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 rounded-full transition-all"
                style={{ width: `${((currentIdx + 1) / total) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">
              已答 {answered}/{total}
            </span>
            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-mono text-sm font-medium ${isTimeWarning ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-600'}`}>
              <Clock className="w-4 h-4" />
              {formatTime(timeLeft)}
            </div>
            <button
              className="btn-secondary !py-1.5 !px-3 text-sm text-red-600 border-red-200 hover:bg-red-50"
              onClick={handleFinish}
            >
              交卷
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Question Area */}
          <div className="lg:col-span-2 space-y-4">
            {/* Question Card */}
            <div className="card p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className={`badge ${
                  current.type === 'single' ? 'bg-blue-100 text-blue-700' :
                  current.type === 'multiple' ? 'bg-amber-100 text-amber-700' :
                  'bg-green-100 text-green-700'
                }`}>
                  {current.type === 'single' ? '单选题' :
                   current.type === 'multiple' ? '多选题' : '判断题'}
                </span>
                <span className="text-xs text-slate-400">第 {current.id} 题</span>
              </div>

              <h2 className="text-base lg:text-lg font-medium text-slate-800 leading-relaxed mb-6 whitespace-pre-wrap">
                {current.question}
              </h2>

              {/* Options */}
              <div className="space-y-3">
                {Object.entries(current.options).map(([key, value]) => {
                  const selected = current.type === 'multiple'
                    ? selectedAnswer.includes(key)
                    : selectedAnswer === key
                  const correct = currentResult?.correct_answer.includes(key) ?? false

                  let cls = 'option-btn-default'
                  if (showAnswer) {
                    if (correct) cls = 'option-btn-correct'
                    else if (selected && !correct) cls = 'option-btn-wrong'
                  } else if (selected) {
                    cls = 'option-btn-selected'
                  }

                  const labelColors: Record<string, string> = {
                    A: 'bg-blue-100 text-blue-700',
                    B: 'bg-green-100 text-green-700',
                    C: 'bg-amber-100 text-amber-700',
                    D: 'bg-purple-100 text-purple-700',
                    E: 'bg-pink-100 text-pink-700',
                  }

                  return (
                    <button
                      key={key}
                      className={cls}
                      onClick={() => { if (!showAnswer) void handleAnswer(key) }}
                      disabled={showAnswer || answerSubmitting}
                    >
                      <div className="flex items-start gap-3">
                        <span className={`shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-sm font-bold ${labelColors[key] || 'bg-slate-100 text-slate-600'}`}>
                          {key}
                        </span>
                        <span className="text-sm leading-relaxed pt-0.5">{value}</span>
                        {showAnswer && correct && (
                          <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 ml-auto" />
                        )}
                        {showAnswer && selected && !correct && (
                          <XCircle className="w-5 h-5 text-red-500 shrink-0 ml-auto" />
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>

              {current.type === 'multiple' && !showAnswer && (
                <button
                  className="btn-primary mt-4"
                  onClick={() => void submitMultipleAnswer()}
                  disabled={!draftAnswers[current.id] || answerSubmitting}
                >
                  {answerSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                  提交多选答案
                </button>
              )}

              {showAnswer && currentResult && !isCorrect && (
                <WrongAnswerExplanation
                  question={{ ...current, answer: currentResult.correct_answer }}
                  userAnswer={userAnswer || ''}
                />
              )}

              {/* Navigation */}
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
                <button
                  className="btn-secondary"
                  onClick={handlePrev}
                  disabled={currentIdx === 0}
                >
                  上一题
                </button>

                {showAnswer ? (
                  <button className="btn-primary" onClick={currentIdx < total - 1 ? handleNext : handleFinish}>
                    {currentIdx < total - 1 ? '下一题' : '查看结果'}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                ) : current.type !== 'multiple' ? (
                  <button className="btn-secondary" disabled>请选择答案</button>
                ) : <span />}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {/* Question Navigator */}
            <div className="card p-4">
              <h3 className="text-sm font-medium text-slate-500 mb-3">答题卡</h3>
              <div className="grid grid-cols-10 gap-1.5 max-h-64 overflow-y-auto scrollbar-thin p-1">
                {questions.map((q, idx) => {
                   const status = answers[q.id] === undefined
                     ? 'unanswered'
                    : answerResults[q.id]?.is_correct
                    ? 'correct'
                    : 'wrong'

                  return (
                    <button
                      key={q.id}
                      onClick={() => {
                        setCurrentIdx(idx)
                        setShowAnswer(Boolean(answerResults[q.id]))
                      }}
                      className={`w-8 h-8 rounded-lg text-xs font-medium flex items-center justify-center transition-all ${
                        idx === currentIdx ? 'ring-2 ring-primary-500 ring-offset-1' : ''
                      } ${
                        status === 'correct' ? 'bg-green-100 text-green-700' :
                        status === 'wrong' ? 'bg-red-100 text-red-700' :
                        'bg-slate-100 text-slate-500 hover:bg-slate-200'
                      }`}
                    >
                      {idx + 1}
                    </button>
                  )
                })}
              </div>
              <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-100 text-xs">
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-100" /> 已对</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-100" /> 已错</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-slate-100" /> 未答</span>
              </div>
            </div>

            {/* Progress */}
            <div className="card p-4">
              <h3 className="text-sm font-medium text-slate-500 mb-2">答题进度</h3>
              <div className="space-y-2">
                {[
                  { label: '已答题数', value: answered, color: 'text-blue-600' },
                  { label: '未答题数', value: total - answered, color: 'text-slate-400' },
                  { label: '当前正确', value: Object.values(answerResults).filter((item) => item.is_correct).length, color: 'text-green-600' },
                ].map((item) => (
                  <div key={item.label} className="flex justify-between text-sm">
                    <span className="text-slate-500">{item.label}</span>
                    <span className={`font-medium ${item.color}`}>{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── Result Phase ─────────────────────────────────────────────────────────
  if (phase === 'result' && result) {
    const scoreData = result.score
    const isPass = scoreData.percentage >= 60

    return (
      <div className="max-w-4xl mx-auto space-y-5">
        {/* Score Header */}
        <div className={`rounded-3xl p-8 text-center text-white ${isPass ? 'bg-gradient-to-br from-green-500 to-emerald-600' : 'bg-gradient-to-br from-orange-500 to-red-600'}`}>
          <Trophy className="w-16 h-16 mx-auto mb-4 opacity-90" />
          <div className="text-5xl font-bold mb-2">{scoreData.percentage}%</div>
          <div className="text-xl font-medium mb-1">{scoreData.grade}</div>
          <div className="text-white/70">
            {scoreData.raw} / {scoreData.max} 分
          </div>
          <div className="flex justify-center gap-6 mt-6 text-sm text-white/80">
            <div>
              <div className="text-2xl font-bold">{result.summary.correct}</div>
              <div>正确</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{result.summary.incorrect}</div>
              <div>错误</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{Math.floor(result.summary.time_seconds / 60)}</div>
              <div>分钟</div>
            </div>
          </div>
        </div>

        {/* Type Breakdown */}
        <div className="card p-5">
          <h3 className="font-medium text-slate-700 mb-4">各题型表现</h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(result.by_type).map(([type, stats]) => (
              <div key={type} className="text-center">
                <div className={`text-3xl font-bold ${
                  type === 'single' ? 'text-blue-600' :
                  type === 'multiple' ? 'text-amber-600' : 'text-green-600'
                }`}>
                  {stats.rate}%
                </div>
                <div className="text-sm text-slate-500">
                  {type === 'single' ? '单选题' :
                   type === 'multiple' ? '多选题' : '判断题'}
                </div>
                <div className="text-xs text-slate-400">
                  {stats.correct}/{stats.total}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          <button className="btn-primary" onClick={handleRestart}>
            <RotateCcw className="w-4 h-4" />
            再来一次
          </button>
          <button className="btn-secondary" onClick={() => navigate('/practice')}>
            <BookOpen className="w-4 h-4" />
            专项练习
          </button>
          <button className="btn-ai" onClick={() => navigate('/ai-summary')}>
            <Sparkles className="w-4 h-4" />
            AI 分析报告
          </button>
        </div>

        {/* Wrong Questions */}
        {result.questions.filter((q) => !q.is_correct).length > 0 && (
          <div className="card p-5">
            <h3 className="font-medium text-slate-700 mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-500" />
              错题回顾 ({result.questions.filter((q) => !q.is_correct).length}题)
            </h3>
            <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-thin">
              {result.questions
                .filter((q) => !q.is_correct)
                .map((q) => (
                  <div key={q.id} className="bg-red-50 rounded-xl p-4">
                    <div className="flex items-start gap-2">
                      <XCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                      <div>
                        <div className="text-sm text-slate-700 mb-2">{q.question}</div>
                        <div className="flex gap-4 text-xs">
                          <span className="text-red-600">
                            你的答案: {q.user_answer || '未答'}
                          </span>
                          <span className="text-green-600">
                            正确答案: {q.correct_answer}
                          </span>
                        </div>
                      </div>
                    </div>
                    <WrongAnswerExplanation
                      question={{
                        id: q.id,
                        type: q.type,
                        question: q.question,
                        options: q.options,
                        answer: q.correct_answer,
                      }}
                      userAnswer={q.user_answer || ''}
                    />
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  return null
}
