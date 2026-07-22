import { useState, useEffect } from 'react'
import { Network, Loader2, RefreshCw } from 'lucide-react'
import { getKnowledgeMap } from '../lib/api'

interface Node {
  id: number
  label: string
  level: number
  parent?: number
  question_count?: number
}

interface Edge {
  source: number
  target: number
  type: string
}

export default function KnowledgeMap() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<{
    nodes: Node[]
    edges: Edge[]
    total_topics?: number
    total_concepts?: number
  } | null>(null)

  const loadMap = async () => {
    setLoading(true)
    try {
      const res = await getKnowledgeMap()
      setData(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMap()
  }, [])

  const rootNodes = data?.nodes?.filter((n) => n.level === 0) || []
  const topicNodes = data?.nodes?.filter((n) => n.level === 1) || []
  const conceptNodes = data?.nodes?.filter((n) => n.level === 2) || []

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Network className="w-6 h-6 text-pink-500" />
            知识地图
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            可视化展示500道题覆盖的知识结构 ({data?.total_topics || 0}个类别, {data?.total_concepts || 0}个概念)
          </p>
        </div>
        <button className="btn-primary text-sm" onClick={loadMap} disabled={loading}>
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> 加载中</> : <><RefreshCw className="w-4 h-4" /> 刷新</>}
        </button>
      </div>

      {loading && !data && (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-12 h-12 text-pink-500 animate-spin mb-4" />
          <p className="text-slate-500">AI知识总结Agent构建知识地图中...</p>
        </div>
      )}

      {data && (
        <div className="space-y-5">
          {/* Root */}
          {rootNodes.map((root) => (
            <div key={root.id}>
              {/* Root Node */}
              <div className="flex justify-center mb-6">
                <div className="bg-gradient-to-br from-pink-500 to-rose-600 text-white px-8 py-4 rounded-2xl shadow-xl shadow-pink-200 text-center">
                  <div className="text-xl font-bold">{root.label}</div>
                  <div className="text-pink-200 text-sm mt-0.5">500题 · 3种题型</div>
                </div>
              </div>

              {/* Topic Nodes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {topicNodes.map((topic) => {
                  const children = conceptNodes.filter((c) => c.parent === topic.id)
                  return (
                    <div key={topic.id} className="relative">
                      {/* Connection line */}
                      <div className="hidden sm:block absolute -top-3 left-1/2 w-px h-3 bg-slate-300 -translate-x-1/2" />

                      <div className="bg-gradient-to-br from-primary-500 to-primary-700 text-white p-4 rounded-2xl shadow-lg">
                        <div className="font-medium text-sm mb-1">{topic.label}</div>
                        {topic.question_count && (
                          <div className="text-xs text-primary-200">{topic.question_count} 题</div>
                        )}

                        {/* Sub-concepts */}
                        {children.length > 0 && (
                          <div className="mt-3 space-y-1.5">
                            {children.map((child) => (
                              <div
                                key={child.id}
                                className="bg-white/15 rounded-lg px-2.5 py-1.5 text-xs text-white/90 flex items-center gap-1.5"
                              >
                                <span className="w-1 h-1 rounded-full bg-white/60" />
                                {child.label}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {data && (
        <div className="card p-5">
          <h3 className="text-sm font-medium text-slate-500 mb-3">知识地图数据</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            <div className="bg-slate-50 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-slate-700">{data.total_topics}</div>
              <div className="text-xs text-slate-500">知识类别</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-slate-700">{data.total_concepts}</div>
              <div className="text-xs text-slate-500">核心概念</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-slate-700">{data.nodes?.length}</div>
              <div className="text-xs text-slate-500">节点数</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-slate-700">{data.edges?.length}</div>
              <div className="text-xs text-slate-500">关系数</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
