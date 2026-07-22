import { useEffect, useState } from 'react'
import {
  BookOpen,
  Target,
  Trophy,
  Zap,
  Brain,
  TrendingUp,
  Award,
  Clock,
  ArrowRight,
  Sparkles,
  Users,
  FileText,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  PenLine,
  Network,
  GalleryVerticalEnd as Flashcards,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import {
  getQuestionStats,
  aiSummarize,
  aiPredict,
  type TopicAnalysis,
} from '../lib/api'
import type { QuestionStats } from '../types'

const FEATURES = [
  {
    icon: PenLine,
    title: '模拟考试',
    desc: '仿真考试环境，倒计时、自动评分、详细解析',
    color: 'from-blue-500 to-indigo-600',
    path: '/exam',
    stat: '500题',
  },
  {
    icon: BookOpen,
    title: '专项练习',
    desc: '按题型分类练习，薄弱点针对性强化',
    color: 'from-emerald-500 to-teal-600',
    path: '/practice',
    stat: '3种题型',
  },
  {
    icon: Sparkles,
    title: 'AI 知识总结',
    desc: '5个AI Agent协作，自动生成知识点总结',
    color: 'from-amber-500 to-orange-600',
    path: '/ai-summary',
    stat: 'Multi-Agent',
  },
  {
    icon: BarChart3,
    title: '学习分析',
    desc: '多维度分析学习数据，识别薄弱知识点',
    color: 'from-purple-500 to-violet-600',
    path: '/analytics',
    stat: 'AI驱动',
  },
  {
    icon: Network,
    title: '知识地图',
    desc: '可视化知识结构，清晰掌握学习路径',
    color: 'from-pink-500 to-rose-600',
    path: '/knowledge',
    stat: '可视化',
  },
  {
    icon: Flashcards,
    title: '知识卡片',
    desc: '卡片式记忆，高效复习核心知识点',
    color: 'from-cyan-500 to-sky-600',
    path: '/flashcards',
    stat: '闪卡模式',
  },
]

const CHART_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']

export default function Home() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<QuestionStats | null>(null)
  const [topicData, setTopicData] = useState<TopicAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    getQuestionStats().then(setStats).finally(() => setLoading(false))
  }, [])

  const handleAISummary = async () => {
    setAiLoading(true)
    try {
      await aiSummarize('topic_analysis')
      navigate('/ai-summary')
    } finally {
      setAiLoading(false)
    }
  }

  const typeColors: Record<string, string> = {
    single: '#3b82f6',
    multiple: '#f59e0b',
    truefalse: '#10b981',
  }

  const typeLabels: Record<string, string> = {
    single: '单选题',
    multiple: '多选题',
    truefalse: '判断题',
  }

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary-700 via-primary-800 to-slate-900 p-8 lg:p-10 text-white">
        <div className="absolute top-0 right-0 w-72 h-72 bg-ai-400/10 rounded-full -translate-y-1/2 translate-x-1/4 blur-2xl" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-primary-400/10 rounded-full translate-y-1/2 -translate-x-1/4 blur-2xl" />

        <div className="relative">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-amber-300" />
            <span className="text-amber-200 text-sm font-medium">
              2026年深圳技能大赛 · 人工智能训练师
            </span>
          </div>
          <h1 className="text-3xl lg:text-4xl font-bold mb-3 leading-tight">
            初赛理论题库
            <span className="bg-gradient-to-r from-amber-200 to-amber-400 bg-clip-text text-transparent">
              智能答题平台
            </span>
          </h1>
          <p className="text-primary-200 text-sm lg:text-base mb-6 max-w-xl">
            基于 Multi-Agent AI 技术的全新学习体验。5个AI Agent 协同工作，
            为你提供知识点总结、学习分析、考点预测等智能服务。
          </p>

          <div className="flex flex-wrap gap-3">
            <button className="btn-primary bg-white text-primary-700 hover:bg-primary-50" onClick={() => navigate('/exam')}>
              <PenLine className="w-4 h-4" />
              开始考试
            </button>
            <button className="btn-primary bg-white/10 border border-white/20 hover:bg-white/20" onClick={handleAISummary} disabled={aiLoading}>
              <Sparkles className="w-4 h-4" />
              {aiLoading ? 'AI生成中...' : 'AI 智能总结'}
            </button>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: '总题量', value: stats?.total ?? '...', icon: FileText, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: '单选题', value: stats?.single ?? '...', icon: BookOpen, color: 'text-amber-600', bg: 'bg-amber-50' },
          { label: '多选题', value: stats?.multiple ?? '...', icon: Target, color: 'text-purple-600', bg: 'bg-purple-50' },
          { label: '判断题', value: stats?.truefalse ?? '...', icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-50' },
        ].map((stat) => (
          <div key={stat.label} className="card p-4">
            <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center mb-3`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div className="text-2xl font-bold text-slate-800">{stat.value}</div>
            <div className="text-sm text-slate-500">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Features Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-500" />
            功能模块
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              onClick={() => navigate(feature.path)}
              className="card-hover p-5 cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-5 h-5 text-white" />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-primary-500 group-hover:translate-x-1 transition-all" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-1">{feature.title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed mb-3">{feature.desc}</p>
              <span className="badge bg-slate-100 text-slate-600">{feature.stat}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Topic Distribution */}
      {topicData.length > 0 && (
        <div>
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-primary-500" />
            知识点分布
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="card p-5">
              <h3 className="text-sm font-medium text-slate-500 mb-4">各知识点题目占比</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={topicData.slice(0, 8)}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="percentage"
                      nameKey="name"
                    >
                      {topicData.slice(0, 8).map((entry, idx) => (
                        <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number, name: string) => [
                        `${value}% - ${name}`,
                        '占比',
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card p-5">
              <h3 className="text-sm font-medium text-slate-500 mb-4">知识点排行</h3>
              <div className="space-y-3">
                {topicData.slice(0, 8).map((topic, idx) => (
                  <div key={topic.name} className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500">
                      {idx + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-slate-700 truncate">{topic.name}</span>
                        <span className="text-xs text-slate-400 ml-2">{topic.percentage}%</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(topic.percentage * 5, 100)}%`,
                            backgroundColor: CHART_COLORS[idx % CHART_COLORS.length],
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tips Section */}
      <div className="card p-6">
        <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2 mb-4">
          <Trophy className="w-5 h-5 text-amber-500" />
          考试技巧
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { icon: Clock, title: '时间管理', tip: '每题约1分钟，留5分钟检查', color: 'text-blue-500' },
            { icon: Target, title: '多选题策略', tip: '不确定时少选比错选更安全', color: 'text-amber-500' },
            { icon: Brain, title: '排除法', tip: '含"一切/所有"的选项通常错误', color: 'text-purple-500' },
            { icon: TrendingUp, title: '优先顺序', tip: '先做判断题→单选题→多选题', color: 'text-green-500' },
          ].map((item) => (
            <div key={item.title} className="bg-slate-50 rounded-xl p-4">
              <item.icon className={`w-5 h-5 ${item.color} mb-2`} />
              <div className="font-medium text-sm text-slate-700">{item.title}</div>
              <div className="text-xs text-slate-500 mt-1">{item.tip}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
