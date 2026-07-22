import { useState, useEffect, useCallback } from 'react'
import { GalleryVerticalEnd as Flashcards, RotateCcw, ChevronLeft, ChevronRight, Shuffle } from 'lucide-react'
import { getKnowledgeCards, type KnowledgeCard } from '../lib/api'

type FilterType = 'all' | 'single' | 'multiple' | 'truefalse'

const FILTERS: { id: FilterType; label: string }[] = [
  { id: 'all', label: '全部' },
  { id: 'single', label: '选择题' },
  { id: 'multiple', label: '多选题' },
  { id: 'truefalse', label: '判断题' },
]

export default function FlashcardsPage() {
  const [cards, setCards] = useState<KnowledgeCard[]>([])
  const [filtered, setFiltered] = useState<KnowledgeCard[]>([])
  const [filter, setFilter] = useState<FilterType>('all')
  const [currentIdx, setCurrentIdx] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [loading, setLoading] = useState(false)

  const loadCards = useCallback(async (type?: string) => {
    setLoading(true)
    try {
      const res = await getKnowledgeCards(type)
      setCards(res.cards)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCards()
  }, [loadCards])

  useEffect(() => {
    const filteredCards = filter === 'all'
      ? cards
      : cards.filter((c) => c.type === filter)
    setFiltered(filteredCards)
    setCurrentIdx(0)
    setFlipped(false)
  }, [filter, cards])

  const current = filtered[currentIdx]
  const hasPrev = currentIdx > 0
  const hasNext = currentIdx < filtered.length - 1

  const goNext = () => {
    if (hasNext) {
      setCurrentIdx((i) => i + 1)
      setFlipped(false)
    }
  }

  const goPrev = () => {
    if (hasPrev) {
      setCurrentIdx((i) => i - 1)
      setFlipped(false)
    }
  }

  const shuffle = () => {
    const shuffled = [...filtered].sort(() => Math.random() - 0.5)
    setFiltered(shuffled)
    setCurrentIdx(0)
    setFlipped(false)
  }

  const typeLabels: Record<string, string> = {
    single: '选择',
    multiple: '多选',
    truefalse: '判断',
  }

  const typeColors: Record<string, string> = {
    single: 'bg-blue-100 text-blue-700',
    multiple: 'bg-amber-100 text-amber-700',
    truefalse: 'bg-green-100 text-green-700',
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto text-center py-20">
        <Flashcards className="w-12 h-12 text-primary-400 animate-pulse mx-auto mb-4" />
        <p className="text-slate-500">加载知识卡片中...</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Flashcards className="w-6 h-6 text-cyan-500" />
          知识卡片
        </h1>
        <p className="text-slate-500 text-sm mt-1">翻转卡片，高效记忆核心知识点</p>
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                filter === f.id
                  ? 'bg-primary-100 text-primary-700 ring-2 ring-primary-300'
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-primary-300'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">{filtered.length} 张卡片</span>
          <button className="btn-secondary !py-1.5 !px-3 text-sm" onClick={shuffle}>
            <Shuffle className="w-3.5 h-3.5" />
            随机
          </button>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-20 text-slate-400">
          <Flashcards className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>该分类暂无卡片</p>
        </div>
      ) : (
        <>
          {/* Card */}
          <div
            onClick={() => setFlipped((f) => !f)}
            className="relative h-72 cursor-pointer group"
            style={{ perspective: '1000px' }}
          >
            <div
              className={`w-full h-full transition-all duration-500 relative`}
              style={{
                transformStyle: 'preserve-3d',
                transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
              }}
            >
              {/* Front */}
              <div
                className="absolute inset-0 backface-hidden rounded-3xl bg-gradient-to-br from-primary-600 to-primary-800 p-8 flex flex-col items-center justify-center text-white shadow-2xl shadow-primary-200"
                style={{ backfaceVisibility: 'hidden' }}
              >
                <div className="flex items-center gap-2 mb-4">
                  <span className={`badge ${typeColors[current?.type] || 'bg-white/20 text-white'} text-xs`}>
                    {typeLabels[current?.type] || current?.type}
                  </span>
                  <span className="text-xs text-primary-200">#{current?.id}</span>
                </div>
                <p className="text-center text-base lg:text-lg leading-relaxed font-medium">
                  {current?.front}
                </p>
                <div className="mt-6 text-xs text-primary-300 animate-pulse">
                  点击卡片查看答案
                </div>
              </div>

              {/* Back */}
              <div
                className="absolute inset-0 backface-hidden rounded-3xl bg-gradient-to-br from-green-500 to-emerald-600 p-8 flex flex-col items-center justify-center text-white shadow-2xl shadow-green-200"
                style={{
                  backfaceVisibility: 'hidden',
                  transform: 'rotateY(180deg)',
                }}
              >
                <div className="text-xs text-green-200 mb-3">正确答案</div>
                <p className="text-center text-lg lg:text-xl leading-relaxed font-medium">
                  {current?.back}
                </p>
                <div className="mt-6 text-xs text-green-200">
                  点击卡片返回
                </div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              className="btn-secondary"
              onClick={goPrev}
              disabled={!hasPrev}
            >
              <ChevronLeft className="w-5 h-5" />
              上一张
            </button>

            <div className="flex items-center gap-1.5">
              {filtered.slice(Math.max(0, currentIdx - 2), currentIdx + 3).map((_, idx) => {
                const actualIdx = Math.max(0, currentIdx - 2) + idx
                const isCurrent = actualIdx === currentIdx
                return (
                  <button
                    key={actualIdx}
                    onClick={() => { setCurrentIdx(actualIdx); setFlipped(false) }}
                    className={`w-2.5 h-2.5 rounded-full transition-all ${
                      isCurrent ? 'bg-primary-500 w-6' : 'bg-slate-300 hover:bg-slate-400'
                    }`}
                  />
                )
              })}
            </div>

            <button
              className="btn-primary"
              onClick={goNext}
              disabled={!hasNext}
            >
              下一张
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          {/* Keyboard hint */}
          <div className="text-center text-xs text-slate-400">
            使用键盘 ← → 翻页 | 空格键 翻转卡片
          </div>
        </>
      )}
    </div>
  )
}
