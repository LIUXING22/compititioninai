import { useEffect, useState } from 'react'
import { AlertCircle, Brain, Lightbulb, Loader2, Sparkles } from 'lucide-react'
import { aiExplain, type AIExplanationResponse, type Question } from '../lib/api'

interface Props {
  question: Question
  userAnswer: string
}

const explanationCache = new Map<string, AIExplanationResponse>()

export default function WrongAnswerExplanation({ question, userAnswer }: Props) {
  const [result, setResult] = useState<AIExplanationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const cacheKey = `${question.id}:${userAnswer}`

  useEffect(() => {
    setResult(explanationCache.get(cacheKey) ?? null)
    setError('')
  }, [cacheKey])

  const loadExplanation = async () => {
    const cached = explanationCache.get(cacheKey)
    if (cached) {
      setResult(cached)
      return
    }

    setLoading(true)
    setError('')
    try {
      const response = await aiExplain(question, userAnswer)
      explanationCache.set(cacheKey, response)
      setResult(response)
    } catch {
      setError('解析暂时不可用，请稍后重试。')
    } finally {
      setLoading(false)
    }
  }

  if (!result) {
    return (
      <div className="mt-4 border-t border-slate-200 pt-4">
        <button className="btn-ai text-sm" onClick={loadExplanation} disabled={loading}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {loading ? '正在分析错因...' : 'AI 解释这道错题'}
        </button>
        {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      </div>
    )
  }

  const { data } = result
  return (
    <section className="mt-4 border-t border-slate-200 pt-4 space-y-3" aria-label="AI错题解析">
      <div className="flex flex-wrap items-center gap-2">
        <Brain className="w-4 h-4 text-emerald-600" />
        <h4 className="text-sm font-semibold text-slate-800">错题解析</h4>
        <span className={`badge ${data.source === 'openai' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
          {data.source === 'openai' ? `OpenAI${result.model ? ` · ${result.model}` : ''}` : '本地解析'}
        </span>
      </div>

      <p className="text-sm font-medium text-slate-800">{data.summary}</p>
      <div className="text-sm text-slate-600 leading-6">
        <span className="font-medium text-slate-700">答案依据：</span>{data.reasoning}
      </div>
      <div className="flex items-start gap-2 text-sm text-amber-800 bg-amber-50 px-3 py-2 rounded-lg">
        <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
        <span><span className="font-medium">错因：</span>{data.mistake_analysis}</span>
      </div>

      {data.knowledge_points.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.knowledge_points.map((point) => (
            <span key={point} className="badge bg-blue-50 text-blue-700">{point}</span>
          ))}
        </div>
      )}

      <div className="flex items-start gap-2 text-sm text-emerald-800">
        <Lightbulb className="w-4 h-4 mt-0.5 shrink-0" />
        <span>{data.study_tip}</span>
      </div>
      {data.fallback_reason && (
        <p className="text-xs text-slate-400">{data.fallback_reason}</p>
      )}
    </section>
  )
}
