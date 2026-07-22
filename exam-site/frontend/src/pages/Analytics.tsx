import { useState, useEffect } from 'react'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  Award,
  Target,
  AlertCircle,
  Loader2,
  RefreshCw,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts'
import {
  aiAnalyze,
  aiFullAnalysis,
  getQuestionStats,
} from '../lib/api'
import type { QuestionStats } from '../types'

const CHART_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899']

export default function Analytics() {
  const [stats, setStats] = useState<QuestionStats | null>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [fullAnalysis, setFullAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'weak' | 'full'>('overview')

  useEffect(() => {
    getQuestionStats().then(setStats)
  }, [])

  const runAnalysis = async (mode = 'full_analysis') => {
    setLoading(true)
    try {
      const res = await aiAnalyze(mode, [
        { question_id: 1, is_correct: true, timestamp: '2026-07-20T10:00:00' },
        { question_id: 2, is_correct: false, timestamp: '2026-07-20T10:05:00' },
        { question_id: 3, is_correct: true, timestamp: '2026-07-21T09:00:00' },
        { question_id: 4, is_correct: true, timestamp: '2026-07-21T09:10:00' },
        { question_id: 5, is_correct: false, timestamp: '2026-07-22T08:00:00' },
      ])
      setAnalysis(res.data)
    } finally {
      setLoading(false)
    }
  }

  const runFullAnalysis = async () => {
    setLoading(true)
    try {
      const res = await aiFullAnalysis({})
      setFullAnalysis(res)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'full' && !fullAnalysis) runFullAnalysis()
  }, [activeTab])

  // Demo data for visualization
  const typeData = stats ? [
    { name: '单选题', value: stats.single, color: '#3b82f6' },
    { name: '多选题', value: stats.multiple, color: '#f59e0b' },
    { name: '判断题', value: stats.truefalse, color: '#10b981' },
  ] : []

  const trendData = [
    { day: 'Day1', rate: 40 },
    { day: 'Day2', rate: 55 },
    { day: 'Day3', rate: 60 },
    { day: 'Day4', rate: 70 },
    { day: 'Day5', rate: 75 },
    { day: 'Day6', rate: 80 },
    { day: 'Day7', rate: 85 },
  ]

  const radarData = [
    { subject: '职业道德', value: 85 },
    { subject: '计算机基础', value: 70 },
    { subject: '网络技术', value: 60 },
    { subject: 'Python', value: 75 },
    { subject: '机器学习', value: 50 },
    { subject: '深度学习', value: 45 },
    { subject: '数据采集', value: 80 },
  ]

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-primary-500" />
            学习分析
          </h1>
          <p className="text-slate-500 text-sm mt-1">AI学习分析Agent提供多维度学习洞察</p>
        </div>
        <button
          className="btn-ai text-sm"
          onClick={() => runAnalysis()}
          disabled={loading}
        >
          {loading ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> 分析中...</>
          ) : (
            <><RefreshCw className="w-4 h-4" /> AI分析</>
          )}
        </button>
      </div>

      {/* Overview Stats */}
      {analysis?.analysis_type === 'full' && analysis?.overview && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            { label: '已答题数', value: analysis.overview.total_answered, color: 'text-blue-600', bg: 'bg-blue-50' },
            { label: '正确', value: analysis.overview.correct, color: 'text-green-600', bg: 'bg-green-50' },
            { label: '错误', value: analysis.overview.incorrect, color: 'text-red-600', bg: 'bg-red-50' },
            { label: '正确率', value: `${analysis.overview.score_rate}%`, color: 'text-primary-600', bg: 'bg-primary-50' },
            { label: '等级', value: analysis.overview.grade, color: 'text-amber-600', bg: 'bg-amber-50' },
          ].map((item) => (
            <div key={item.label} className={`card p-4 ${item.bg} border-0`}>
              <div className="text-xs text-slate-500 mb-1">{item.label}</div>
              <div className={`text-2xl font-bold ${item.color}`}>{item.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        {[
          { key: 'overview', label: '数据总览' },
          { key: 'weak', label: '薄弱分析' },
          { key: 'full', label: 'AI全部分析' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-primary-500 text-primary-700'
                : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Trend Chart */}
          <div className="card p-5">
            <h3 className="text-sm font-medium text-slate-500 mb-4">正确率趋势</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="day" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                  <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" domain={[0, 100]} />
                  <Tooltip formatter={(value: any) => [`${value}%`, '正确率']} />
                  <Line type="monotone" dataKey="rate" stroke="#3b82f6" strokeWidth={3}
                        dot={{ fill: '#3b82f6', r: 4 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Radar Chart */}
          <div className="card p-5">
            <h3 className="text-sm font-medium text-slate-500 mb-4">知识掌握度</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <PolarRadiusAxis tick={{ fontSize: 11 }} domain={[0, 100]} stroke="#94a3b8" />
                  <Radar name="掌握度" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Question Type Pie */}
          <div className="card p-5">
            <h3 className="text-sm font-medium text-slate-500 mb-4">题库构成</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={typeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {typeData.map((entry, idx) => (
                      <Cell key={idx} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any, name: string) => [`${value}题`, name]} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 mt-2">
              {typeData.map((item) => (
                <div key={item.name} className="flex items-center gap-1.5 text-xs">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-slate-600">{item.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Performance by type */}
          {analysis?.by_type && (
            <div className="card p-5">
              <h3 className="text-sm font-medium text-slate-500 mb-4">各题型表现</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={Object.entries(analysis.by_type).map(([k, v]: [string, any]) => ({
                    name: k === 'single' ? '单选题' : k === 'multiple' ? '多选题' : '判断题',
                    rate: v.rate,
                    correct: v.correct,
                    total: v.total,
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                    <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" domain={[0, 100]} />
                    <Tooltip formatter={(value: any) => [`${value}%`, '正确率']} />
                    <Bar dataKey="rate" radius={[4, 4, 0, 0]}>
                      {Object.entries(analysis.by_type).map(([, v]: [string, any], idx) => (
                        <Cell key={idx} fill={CHART_COLORS[idx]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'weak' && (
        <div className="card p-5">
          <h3 className="font-medium text-slate-700 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            薄弱知识点分析
          </h3>
          {analysis?.weak_points ? (
            <div className="space-y-3">
              {analysis.weak_points.map((wp: any) => (
                <div key={wp.id} className={`flex items-start gap-3 p-4 rounded-xl ${
                  wp.priority === 'high' ? 'bg-red-50 border border-red-200' : 'bg-amber-50 border border-amber-200'
                }`}>
                  <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium ${
                    wp.priority === 'high' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                  }`}>
                    {wp.priority === 'high' ? '高优先级' : '中优先级'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-slate-700 mb-1 line-clamp-2">{wp.question}</div>
                    <div className="text-xs text-slate-500">
                      错误 {wp.wrong_count} 次 · 类型: {wp.type}
                    </div>
                  </div>
                  <TrendingDown className="w-4 h-4 text-red-400 shrink-0" />
                </div>
              ))}
            </div>
          ) : (
            <button className="btn-secondary" onClick={() => runAnalysis('weak_points')}>
              分析薄弱点
            </button>
          )}
        </div>
      )}

      {activeTab === 'full' && (
        <div className="space-y-4">
          {fullAnalysis?.results ? (
            <>
              <div className="card p-5 bg-gradient-to-br from-primary-50 to-ai-50">
                <div className="text-sm font-medium text-slate-600 mb-1">AI 全部分析完成</div>
                <div className="text-xs text-slate-500">
                  用时 {fullAnalysis.total_ms?.toFixed(0) || 0}ms · Agents: {fullAnalysis.agents_used?.join(', ')}
                </div>
              </div>

              {fullAnalysis.results.summarizer?.data?.topic_distribution && (
                <div className="card p-5">
                  <h3 className="font-medium text-slate-700 mb-3">知识点分布 (AI Summarizer)</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                    {fullAnalysis.results.summarizer.data.topic_distribution.topics?.slice(0, 8).map((t: any) => (
                      <div key={t.name} className="bg-slate-50 rounded-lg p-2.5">
                        <div className="text-sm font-medium text-slate-700 truncate">{t.name}</div>
                        <div className="text-xs text-slate-500">{t.percentage}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {fullAnalysis.results.analyzer?.data?.suggestions && (
                <div className="card p-5">
                  <h3 className="font-medium text-slate-700 mb-3">AI学习建议</h3>
                  <div className="space-y-2">
                    {fullAnalysis.results.analyzer.data.suggestions.map((sug: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-slate-700 bg-amber-50 rounded-lg px-3 py-2">
                        <span className="text-amber-500 shrink-0">•</span>
                        {sug}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12">
              <button className="btn-ai" onClick={runFullAnalysis} disabled={loading}>
                {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> AI全部分析...</> : <><BarChart3 className="w-4 h-4" /> 运行AI全部分析</>}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
