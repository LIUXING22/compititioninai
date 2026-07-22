import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  BookOpen,
  Target,
  RotateCcw,
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
} from 'lucide-react'
import {
  startPractice,
  type Question,
} from '../lib/api'
import WrongAnswerExplanation from '../components/WrongAnswerExplanation'

type PracticeMode =
  | 'sequential'
  | 'random'
  | 'by_type_single'
  | 'by_type_multiple'
  | 'by_type_truefalse'

const MODES: { id: PracticeMode; label: string; desc: string }[] = [
  { id: 'sequential', label: '顺序练习', desc: '按题号顺序 1-500' },
  { id: 'random', label: '随机练习', desc: '随机抽取 20 道题' },
  { id: 'by_type_single', label: '单选题专练', desc: '300 道单选题' },
  { id: 'by_type_multiple', label: '多选题专练', desc: '70 道多选题' },
  { id: 'by_type_truefalse', label: '判断题专练', desc: '130 道判断题' },
]

const MODE_TYPE_MAP: Record<PracticeMode, string[]> = {
  sequential: ['single', 'multiple', 'truefalse'],
  random: ['single', 'multiple', 'truefalse'],
  by_type_single: ['single'],
  by_type_multiple: ['multiple'],
  by_type_truefalse: ['truefalse'],
}

type Phase = 'setup' | 'active' | 'review'

export default function Practice() {
  const navigate = useNavigate()
  const [phase, setPhase] = useState<Phase>('setup')
  const [mode, setMode] = useState<PracticeMode>('random')
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [draftAnswers, setDraftAnswers] = useState<Record<number, string>>({})
  const [showResult, setShowResult] = useState(false)
  const [loading, setLoading] = useState(false)
  const [reviewMode, setReviewMode] = useState(false)

  const current = questions[currentIdx]

  const start = async () => {
    setLoading(true)
    try {
      const types = MODE_TYPE_MAP[mode]
      const count = mode === 'sequential' ? 500
        : mode === 'by_type_single' ? 300
        : mode === 'by_type_multiple' ? 70
        : mode === 'by_type_truefalse' ? 130 : 20

      const res = await startPractice(mode, count, types)
      setQuestions(res.questions)
      setCurrentIdx(0)
      setAnswers({})
      setDraftAnswers({})
      setShowResult(false)
      setReviewMode(false)
      setPhase('active')
    } finally {
      setLoading(false)
    }
  }

  const answer = (ans: string) => {
    if (showResult) return
    if (current.type === 'multiple') {
      setDraftAnswers((prev) => {
        const selected = new Set((prev[current.id] || '').split('').filter(Boolean))
        selected.has(ans) ? selected.delete(ans) : selected.add(ans)
        return { ...prev, [current.id]: [...selected].sort().join('') }
      })
      return
    }
    setAnswers((prev) => ({ ...prev, [current.id]: ans }))
    setShowResult(true)
  }

  const submitMultipleAnswer = () => {
    const answerValue = draftAnswers[current.id]
    if (!answerValue) return
    setAnswers((prev) => ({ ...prev, [current.id]: answerValue }))
    setShowResult(true)
  }

  const next = () => {
    if (currentIdx < questions.length - 1) {
      const nextIndex = currentIdx + 1
      setCurrentIdx(nextIndex)
      setShowResult(answers[questions[nextIndex].id] !== undefined)
    } else {
      handleReview()
    }
  }

  const prev = () => {
    if (currentIdx > 0) {
      const previousIndex = currentIdx - 1
      setCurrentIdx(previousIndex)
      setShowResult(answers[questions[previousIndex].id] !== undefined)
    }
  }

  const handleReview = () => {
    setReviewMode(true)
    setPhase('review')
  }

  const reviewStart = () => {
    setCurrentIdx(0)
    setAnswers({})
    setDraftAnswers({})
    setShowResult(false)
    setReviewMode(false)
    setPhase('active')
  }

  const answered = Object.keys(answers).length
  const correct = questions.filter((q) => answers[q.id] === q.answer).length
  const score = answered > 0 ? Math.round((correct / answered) * 100) : 0

  // ── Setup ────────────────────────────────────────────────────────────────
  if (phase === 'setup') {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-emerald-200">
            <BookOpen className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mb-2">练习模式</h1>
          <p className="text-slate-500 text-sm">选择练习模式，按自己的节奏学习</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`text-left p-4 rounded-xl border-2 transition-all ${
                mode === m.id
                  ? 'border-primary-500 bg-primary-50 shadow-md'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <div className="font-medium text-slate-800 text-sm">{m.label}</div>
              <div className="text-xs text-slate-500 mt-1">{m.desc}</div>
            </button>
          ))}
        </div>

        <button
          className="btn-primary w-full py-3 text-lg"
          onClick={start}
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              加载中...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              开始练习
            </>
          )}
        </button>
      </div>
    )
  }

  // ── Review Phase ─────────────────────────────────────────────────────────
  if (phase === 'review' && reviewMode) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-slate-800">练习回顾</h2>
            <button className="btn-primary !py-1.5 !px-4 text-sm" onClick={reviewStart}>
              <RotateCcw className="w-4 h-4" />
              重新练习
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-blue-50 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">{questions.length}</div>
              <div className="text-xs text-slate-500">总题数</div>
            </div>
            <div className="bg-green-50 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-green-600">{correct}</div>
              <div className="text-xs text-slate-500">正确</div>
            </div>
            <div className="bg-red-50 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-red-600">{questions.length - correct}</div>
              <div className="text-xs text-slate-500">错误</div>
            </div>
          </div>

          <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all"
              style={{ width: `${score}%` }}
            />
          </div>
          <div className="text-center text-sm text-slate-500 mt-2">
            正确率: {score}%
          </div>
        </div>

        <div className="space-y-3">
          {questions.map((q, idx) => {
            const userAns = answers[q.id]
            const isCorrect = userAns === q.answer
            return (
              <div
                key={q.id}
                className={`card p-4 ${
                  isCorrect ? 'border-green-200 bg-green-50/30' : 'border-red-200 bg-red-50/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="shrink-0 w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-600">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-slate-700 mb-2">{q.question}</div>
                    <div className="text-xs text-slate-400">
                      正确答案: <span className="text-green-600 font-medium">
                        {q.type === 'multiple' ? q.answer.split('').map(c => c + ': ' + q.options[c]).join(', ') : q.answer + ': ' + q.options[q.answer]}
                      </span>
                      {userAns && <span className="ml-3 text-red-500">
                        你的答案: {userAns}
                      </span>}
                    </div>
                  </div>
                  {isCorrect ? (
                    <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500 shrink-0" />
                  )}
                </div>
                {!isCorrect && (
                  <WrongAnswerExplanation question={q} userAnswer={userAns || ''} />
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  // ── Active Phase ─────────────────────────────────────────────────────────
  if (phase === 'active' && current) {
    const userAns = answers[current.id]
    const selectedAnswer = current.type === 'multiple' && !showResult
      ? (draftAnswers[current.id] || '')
      : (userAns || '')
    const isCorrect = userAns === current.answer

    return (
      <div className="max-w-3xl mx-auto">
        {/* Top bar */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-slate-500">
            {currentIdx + 1} / {questions.length}
          </span>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">
              已对 {correct} / 已答 {answered}
            </span>
            <span className={`text-sm font-medium ${score >= 60 ? 'text-green-600' : 'text-amber-600'}`}>
              {score}%
            </span>
            <button className="btn-ai !py-1.5 !px-4 text-sm" onClick={handleReview} disabled={answered === 0}>
              {answered > 0 ? '查看回顾' : '答题后查看'}
            </button>
          </div>
        </div>

        {/* Progress */}
        <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden mb-5">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full transition-all"
            style={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }}
          />
        </div>

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
          </div>

          <h2 className="text-base font-medium text-slate-800 leading-relaxed mb-6 whitespace-pre-wrap">
            {current.question}
          </h2>

          <div className="space-y-3">
            {Object.entries(current.options).map(([key, value]) => {
              const selected = current.type === 'multiple'
                ? selectedAnswer.includes(key)
                : selectedAnswer === key
              const correct = current.answer.includes(key)

              let cls = 'option-btn-default'
              if (showResult) {
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
                  onClick={() => answer(key)}
                  disabled={showResult}
                >
                  <div className="flex items-start gap-3">
                    <span className={`shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-sm font-bold ${labelColors[key] || 'bg-slate-100'}`}>
                      {key}
                    </span>
                    <span className="text-sm leading-relaxed pt-0.5">{value}</span>
                    {showResult && correct && (
                      <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 ml-auto" />
                    )}
                    {showResult && selected && !correct && (
                      <XCircle className="w-5 h-5 text-red-500 shrink-0 ml-auto" />
                    )}
                  </div>
                </button>
              )
            })}
          </div>

          {current.type === 'multiple' && !showResult && (
            <button
              className="btn-primary mt-4"
              onClick={submitMultipleAnswer}
              disabled={!draftAnswers[current.id]}
            >
              提交多选答案
            </button>
          )}

          {showResult && !isCorrect && (
            <WrongAnswerExplanation question={current} userAnswer={userAns || ''} />
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-6 pt-4 border-t border-slate-100">
            <button className="btn-secondary" onClick={prev} disabled={currentIdx === 0}>
              上一题
            </button>
            {showResult ? (
              <button className="btn-primary" onClick={next}>
                {currentIdx < questions.length - 1 ? '下一题' : '完成'}
                {currentIdx < questions.length - 1 && <ArrowRight className="w-4 h-4" />}
              </button>
            ) : current.type !== 'multiple' ? (
              <button className="btn-secondary" disabled>
                请选择答案
              </button>
            ) : <span />}
          </div>
        </div>
      </div>
    )
  }

  return null
}
