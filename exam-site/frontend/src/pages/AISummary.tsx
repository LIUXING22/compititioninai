import { useState, useEffect } from 'react'
import {
  Sparkles,
  Brain,
  Loader2,
  FileText,
  BookOpen,
  Network,
  Layers,
  Award,
  ChevronRight,
  RefreshCw,
} from 'lucide-react'
import {
  aiSummarize,
  aiPredict,
  aiPlan,
  type TopicAnalysis,
} from '../lib/api'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'

type SummaryMode = 'full_summary' | 'topic_analysis' | 'knowledge_map' | 'knowledge_cards' | 'chapter_summary'
type PredictionMode = 'full_prediction' | 'high_frequency' | 'key_points' | 'review_plan'
type PlanMode = 'exam_prep'

const SUMMARY_MODES: { id: SummaryMode; label: string; icon: any; desc: string }[] = [
  { id: 'full_summary', label: '全面总结', icon: FileText, desc: '完整知识总结' },
  { id: 'topic_analysis', label: '知识点分析', icon: Layers, desc: '各知识点分布' },
  { id: 'knowledge_map', label: '知识地图', icon: Network, desc: '知识结构图' },
  { id: 'knowledge_cards', label: '知识卡片', icon: BookOpen, desc: '闪卡式学习' },
]

const COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

export default function AISummary() {
  const [summaryMode, setSummaryMode] = useState<SummaryMode>('topic_analysis')
  const [predictionMode, setPredictionMode] = useState<PredictionMode>('high_frequency')
  const [activeTab, setActiveTab] = useState<'summary' | 'prediction' | 'plan'>('summary')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [summaryData, setSummaryData] = useState<any>(null)
  const [predictionData, setPredictionData] = useState<any>(null)
  const [planData, setPlanData] = useState<any>(null)
  const [planParams, setPlanParams] = useState({
    exam_date: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
    daily_minutes: 30,
    current_level: 'beginner',
  })

  useEffect(() => {
    handleSummary()
  }, [summaryMode])

  const handleSummary = async () => {
    setLoading(true)
    setError(null)
    setSummaryData(null)
    try {
      const res = await aiSummarize(summaryMode)
      setSummaryData(res.data)
    } catch (e: any) {
      console.error('AI Summary error:', e)
      setError(e?.message || 'AI总结请求失败')
    } finally {
      setLoading(false)
    }
  }

  const handlePrediction = async () => {
    setLoading(true)
    setError(null)
    setPredictionData(null)
    try {
      const res = await aiPredict(predictionMode)
      setPredictionData(res.data)
    } catch (e: any) {
      console.error('AI Predict error:', e)
      setError(e?.message || 'AI预测请求失败')
    } finally {
      setLoading(false)
    }
  }

  const handlePlan = async () => {
    setLoading(true)
    setError(null)
    setPlanData(null)
    try {
      const res = await aiPlan('exam_prep', planParams.exam_date, planParams.daily_minutes, planParams.current_level)
      setPlanData(res.data)
    } catch (e: any) {
      console.error('AI Plan error:', e)
      setError(e?.message || 'AI规划请求失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'prediction' && !predictionData) handlePrediction()
  }, [activeTab])

  useEffect(() => {
    if (activeTab === 'plan' && !planData) handlePlan()
  }, [activeTab])

  // ── Render Summary ───────────────────────────────────────────────────────
  const renderSummary = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-12 h-12 text-primary-500 animate-spin mb-4" />
          <p className="text-slate-500">AI Agent 正在分析 {summaryMode === 'knowledge_map' ? '知识地图' : summaryMode === 'knowledge_cards' ? '知识卡片' : '知识点'}...</p>
        </div>
      )
    }

    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          <strong>请求失败：</strong>{error}
        </div>
      )
    }

    if (!summaryData) {
      return (
        <div className="text-center py-20 text-slate-400">
          <Brain className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>点击上方模式开始AI总结</p>
        </div>
      )
    }

    // Guard: if data doesn't have expected structure, show raw data
    const hasTopics = Array.isArray(summaryData.topics)
    const hasChapters = Array.isArray(summaryData.chapters)
    const hasNodes = Array.isArray(summaryData.nodes)
    const hasCards = Array.isArray(summaryData.cards)

    if (summaryMode === 'topic_analysis' && !hasTopics) {
      return (
        <div className="text-center py-10 text-slate-400">
          <p>未获取到知识点数据</p>
          <pre className="text-xs mt-2 bg-slate-50 rounded p-3 text-left overflow-auto max-h-40">
            {JSON.stringify(summaryData, null, 2).slice(0, 300)}
          </pre>
        </div>
      )
    }

    // Topic Analysis
    if (summaryMode === 'topic_analysis' && summaryData.topics) {
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
            <div className="card p-4 text-center">
              <div className="text-2xl font-bold text-primary-600">{summaryData.topics?.length || 0}</div>
              <div className="text-xs text-slate-500">知识点分类</div>
            </div>
            <div className="card p-4 text-center">
              <div className="text-2xl font-bold text-ai-600">500</div>
              <div className="text-xs text-slate-500">题目总数</div>
            </div>
            <div className="card p-4 text-center">
              <div className="text-2xl font-bold text-amber-600">
                {summaryData.topics?.[0]?.name || '-'}
              </div>
              <div className="text-xs text-slate-500">最大考点</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="card p-5">
              <h3 className="text-sm font-medium text-slate-500 mb-4">知识点占比分布</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={summaryData.topics?.slice(0, 10)}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="percentage"
                      nameKey="name"
                    >
                      {summaryData.topics?.slice(0, 10).map((_: any, idx: number) => (
                        <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any, name: string) => [`${value}%`, name]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card p-5">
              <h3 className="text-sm font-medium text-slate-500 mb-4">知识点排行</h3>
              <div className="space-y-2.5 max-h-72 overflow-y-auto scrollbar-thin">
                {summaryData.topics?.map((topic: any, idx: number) => (
                  <div key={topic.name} className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
                          style={{ backgroundColor: COLORS[idx % COLORS.length] }}>
                      {idx + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-slate-700 truncate">{topic.name}</span>
                        <span className="text-xs text-slate-400 ml-2">{topic.percentage}%</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{ width: `${topic.percentage * 5}%`, backgroundColor: COLORS[idx % COLORS.length] }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )
    }

    // Full Summary
    if (summaryData.chapters) {
      return (
        <div className="space-y-4">
          <div className="card p-4 bg-primary-50 border-primary-200">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary-600" />
              <div>
                <div className="font-medium text-primary-800 text-sm">AI知识总结</div>
                <div className="text-xs text-primary-600">共 {summaryData.total_topics} 个知识点分类，难度: {summaryData.overall_difficulty}</div>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {summaryData.chapters?.map((ch: any) => (
              <div key={ch.topic} className="card p-4">
                <div className="font-medium text-slate-800 mb-1">{ch.topic}</div>
                <div className="text-xs text-slate-500 mb-3">{ch.total_questions} 题 · {ch.difficulty}</div>
                <div className="flex gap-2 mb-3">
                  <span className="badge bg-blue-100 text-blue-700">{ch.single_choice}单</span>
                  <span className="badge bg-amber-100 text-amber-700">{ch.multiple_choice}多</span>
                  <span className="badge bg-green-100 text-green-700">{ch.true_false}判</span>
                </div>
                <div className="space-y-1">
                  {ch.key_concepts?.slice(0, 3).map((concept: string, i: number) => (
                    <div key={i} className="text-xs bg-slate-50 rounded-lg px-2 py-1 text-slate-600">
                      {concept}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )
    }

    // Knowledge Map
    if (summaryData.nodes) {
      return (
        <div className="card p-6">
          <h3 className="font-medium text-slate-700 mb-4">知识地图</h3>
          <div className="space-y-2">
            {summaryData.nodes?.filter((n: any) => n.level <= 1).map((node: any) => (
              <div key={node.id} className="ml-0">
                <div className="bg-primary-50 rounded-xl px-4 py-3 border border-primary-200">
                  <div className="font-medium text-primary-800 text-sm">{node.label}</div>
                  {node.question_count && (
                    <div className="text-xs text-primary-600">{node.question_count} 题</div>
                  )}
                </div>
                {summaryData.nodes?.filter((n: any) => n.parent === node.id).map((child: any) => (
                  <div key={child.id} className="ml-6 mt-2">
                    <div className="bg-slate-50 rounded-lg px-3 py-2 border border-slate-200">
                      <div className="text-sm text-slate-700">{child.label}</div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div className="mt-4 text-xs text-slate-400">
            共 {summaryData.total_topics} 个知识类别，{summaryData.total_concepts} 个核心概念
          </div>
        </div>
      )
    }

    // Knowledge Cards
    if (summaryData.cards) {
      return (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-slate-700">知识卡片 ({summaryData.cards?.length})</h3>
            <span className="text-xs text-slate-400">点击卡片翻转查看答案</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-[500px] overflow-y-auto scrollbar-thin">
            {summaryData.cards?.slice(0, 30).map((card: any) => (
              <div key={card.id} className="bg-gradient-to-br from-slate-50 to-white border border-slate-200 rounded-xl p-4 hover:shadow-md transition-shadow cursor-pointer">
                <div className="text-xs text-slate-400 mb-1">#{card.id} {card.type === 'truefalse' ? '判断' : '选择'}</div>
                <div className="text-sm text-slate-700 mb-2 line-clamp-2">{card.front}</div>
                <div className="border-t border-slate-200 pt-2 text-sm text-green-700 font-medium">
                  {card.back}
                </div>
              </div>
            ))}
          </div>
        </div>
      )
    }

    return (
      <div className="text-center py-20 text-slate-400">
        <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <pre className="text-xs text-left bg-slate-50 rounded-xl p-4 max-h-64 overflow-auto">
          {JSON.stringify(summaryData, null, 2)}
        </pre>
      </div>
    )
  }

  // ── Render Prediction ────────────────────────────────────────────────────
  const renderPrediction = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-12 h-12 text-amber-500 animate-spin mb-4" />
          <p className="text-slate-500">AI考点预测Agent分析中...</p>
        </div>
      )
    }

    if (!predictionData) {
      return (
        <div className="text-center py-20 text-slate-400">
          <Award className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>点击"生成预测"查看AI考点分析</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {/* High Frequency Topics */}
        {predictionData.high_frequency && (
          <div className="card p-5">
            <h3 className="font-medium text-slate-700 mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-amber-500" />
              高频考点排行
            </h3>
            <div className="space-y-3">
              {predictionData.high_frequency.topics?.map((topic: any, idx: number) => (
                <div key={topic.topic} className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0"
                        style={{ backgroundColor: COLORS[idx % COLORS.length] }}>
                    {topic.rank}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-slate-700 font-medium">{topic.topic}</span>
                      <span className="text-xs text-slate-400">{topic.question_count}题 ({topic.percentage}%)</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${topic.percentage * 8}%`, backgroundColor: COLORS[idx % COLORS.length] }}
                      />
                    </div>
                    <span className="text-xs text-slate-500 mt-0.5">{topic.importance}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Points */}
        {predictionData.key_points && (
          <div className="card p-5">
            <h3 className="font-medium text-slate-700 mb-3">重点题目 ({predictionData.key_points.total_key})</h3>
            <div className="space-y-2 max-h-72 overflow-y-auto scrollbar-thin">
              {predictionData.key_points.questions?.map((q: any) => (
                <div key={q.id} className="bg-slate-50 rounded-xl px-4 py-3 flex items-center gap-3">
                  <span className={`badge ${q.type === 'single' ? 'bg-blue-100 text-blue-700' : q.type === 'multiple' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
                    {q.type === 'single' ? '单' : q.type === 'multiple' ? '多' : '判'}
                  </span>
                  <span className="text-sm text-slate-700 flex-1 line-clamp-1">{q.text}</span>
                  <ChevronRight className="w-4 h-4 text-slate-300" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Review Plan */}
        {predictionData.review_plan && (
          <div className="card p-5">
            <h3 className="font-medium text-slate-700 mb-3">AI复习计划</h3>
            <div className="space-y-2">
              {predictionData.review_plan.plan?.map((item: any) => (
                <div key={item.order} className="flex items-center gap-3 bg-slate-50 rounded-xl px-4 py-3">
                  <span className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-sm font-bold text-primary-700 shrink-0">
                    {item.order}
                  </span>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-slate-700">{item.topic}</div>
                    <div className="text-xs text-slate-500">{item.priority} · {item.action}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // ── Render Plan ──────────────────────────────────────────────────────────
  const renderPlan = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-12 h-12 text-green-500 animate-spin mb-4" />
          <p className="text-slate-500">学习规划Agent生成计划中...</p>
        </div>
      )
    }

    if (!planData) {
      return (
        <div className="text-center py-20 text-slate-400">
          <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>设置参数后点击"生成计划"</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <div className="card p-5 bg-gradient-to-br from-ai-50 to-emerald-50 border-ai-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-ai-700">{planData.days_left}</div>
              <div className="text-xs text-slate-500">剩余天数</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-ai-700">{planData.total_hours}h</div>
              <div className="text-xs text-slate-500">预计总学习</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-ai-700">{planData.daily_minutes}min</div>
              <div className="text-xs text-slate-500">每日学习</div>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          {planData.daily_plans?.map((day: any) => (
            <div key={day.day} className="card p-4 flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-sm font-bold text-primary-700 shrink-0">
                D{day.day}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-slate-700">{day.phase}</span>
                  <span className="badge bg-primary-100 text-primary-700 text-[10px]">{day.focus}</span>
                </div>
                <div className="text-xs text-slate-500">
                  {day.target_questions} 题 · {day.estimated_minutes} 分钟
                </div>
                <div className="text-xs text-ai-600 mt-1">💡 {day.study_tips}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-amber-500" />
          AI 智能总结
        </h1>
        <p className="text-slate-500 text-sm mt-1">5个AI Agent协同工作，为你提供全方位的学习智能服务</p>
      </div>

      {/* Agents Info Bar */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="w-4 h-4 text-primary-600" />
          <span className="text-sm font-medium text-slate-700">在线AI Agents</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            { name: '知识总结Agent', color: 'bg-blue-100 text-blue-700' },
            { name: '题目解析Agent', color: 'bg-purple-100 text-purple-700' },
            { name: '学习分析Agent', color: 'bg-green-100 text-green-700' },
            { name: '考点预测Agent', color: 'bg-amber-100 text-amber-700' },
            { name: '学习规划Agent', color: 'bg-pink-100 text-pink-700' },
          ].map((agent) => (
            <span key={agent.name} className={`badge ${agent.color}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-current mr-1 animate-pulse" />
              {agent.name}
            </span>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">
          <strong>AI请求失败：</strong>{error}
          <button className="ml-3 text-red-500 underline text-xs" onClick={() => setError(null)}>关闭</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        {[
          { key: 'summary', label: '知识总结', icon: FileText },
          { key: 'prediction', label: '考点预测', icon: Award },
          { key: 'plan', label: '学习计划', icon: BookOpen },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-primary-500 text-primary-700'
                : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'summary' && (
        <div className="space-y-4">
          {/* Mode Selector */}
          <div className="flex flex-wrap gap-2">
            {SUMMARY_MODES.map((mode) => (
              <button
                key={mode.id}
                onClick={() => setSummaryMode(mode.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  summaryMode === mode.id
                    ? 'bg-primary-100 text-primary-700 ring-2 ring-primary-300'
                    : 'bg-white text-slate-600 border border-slate-200 hover:border-primary-300'
                }`}
              >
                <mode.icon className="w-4 h-4" />
                {mode.label}
              </button>
            ))}
          </div>
          <button
            className="btn-ai text-sm"
            onClick={handleSummary}
            disabled={loading}
          >
            {loading ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> AI生成中...</>
            ) : (
              <><RefreshCw className="w-4 h-4" /> 生成{SUMMARY_MODES.find(m => m.id === summaryMode)?.label}</>
            )}
          </button>
          {renderSummary()}
        </div>
      )}

      {activeTab === 'prediction' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'high_frequency', label: '高频考点' },
              { id: 'key_points', label: '重点题目' },
              { id: 'review_plan', label: '复习计划' },
            ].map((mode) => (
              <button
                key={mode.id}
                onClick={() => {
                  setPredictionMode(mode.id as PredictionMode)
                  handlePrediction()
                }}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  predictionMode === mode.id
                    ? 'bg-amber-100 text-amber-700 ring-2 ring-amber-300'
                    : 'bg-white text-slate-600 border border-slate-200'
                }`}
              >
                {mode.label}
              </button>
            ))}
          </div>
          <button className="btn-primary !bg-gradient-to-r !from-amber-500 !to-orange-500" onClick={handlePrediction} disabled={loading}>
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> 预测中...</> : <><Award className="w-4 h-4" /> 生成预测</>}
          </button>
          {renderPrediction()}
        </div>
      )}

      {activeTab === 'plan' && (
        <div className="space-y-4">
          <div className="card p-5">
            <h3 className="text-sm font-medium text-slate-700 mb-3">计划参数</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-slate-500 block mb-1">考试日期</label>
                <input
                  type="date"
                  value={planParams.exam_date}
                  onChange={(e) => setPlanParams({ ...planParams, exam_date: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-slate-500 block mb-1">每日学习(分钟)</label>
                <input
                  type="number"
                  value={planParams.daily_minutes}
                  onChange={(e) => setPlanParams({ ...planParams, daily_minutes: Number(e.target.value) })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-slate-500 block mb-1">当前水平</label>
                <select
                  value={planParams.current_level}
                  onChange={(e) => setPlanParams({ ...planParams, current_level: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="beginner">初级</option>
                  <option value="intermediate">中级</option>
                  <option value="advanced">高级</option>
                </select>
              </div>
            </div>
            <button className="btn-primary mt-4" onClick={handlePlan} disabled={loading}>
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> 生成中...</> : <><Sparkles className="w-4 h-4" /> AI生成学习计划</>}
            </button>
          </div>
          {renderPlan()}
        </div>
      )}
    </div>
  )
}
