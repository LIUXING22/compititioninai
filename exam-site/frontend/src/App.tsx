import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  PenLine,
  BookOpen,
  Sparkles,
  BarChart3,
  Network,
  GalleryVerticalEnd as Flashcards,
  Search,
  Menu,
  X,
  GraduationCap,
} from 'lucide-react'

// Pages
import Home from './pages/Home'
import Exam from './pages/Exam'
import Practice from './pages/Practice'
import AISummary from './pages/AISummary'
import Analytics from './pages/Analytics'
import KnowledgeMap from './pages/KnowledgeMap'
import FlashcardsPage from './pages/Flashcards'

// RAG Chat Widget
import ChatWidget from './components/ChatWidget'

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: '首页' },
  { path: '/exam', icon: PenLine, label: '模拟考试' },
  { path: '/practice', icon: BookOpen, label: '练习模式' },
  { path: '/ai-summary', icon: Sparkles, label: 'AI总结' },
  { path: '/analytics', icon: BarChart3, label: '学习分析' },
  { path: '/knowledge', icon: Network, label: '知识地图' },
  { path: '/flashcards', icon: Flashcards, label: '知识卡片' },
]

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 10)
    window.addEventListener('scroll', handler)
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-64 bg-white border-r border-slate-200
          transform transition-transform duration-300 flex flex-col
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-100">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-600 to-ai-500
                          flex items-center justify-center shadow-lg shadow-primary-200">
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm text-slate-800 leading-tight">
              智能答题平台
            </h1>
            <p className="text-[10px] text-slate-400">Multi-Agent AI</p>
          </div>
          <button
            className="ml-auto lg:hidden p-1"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto scrollbar-thin">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                isActive ? 'sidebar-link-active' : 'sidebar-link'
              }
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon className="w-[18px] h-[18px]" />
              <span className="text-sm">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100">
          <div className="flex items-center gap-2 px-2">
            <Search className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-400">
              共500题 | 3种题型
            </span>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 min-w-0 overflow-auto">
        {/* Top bar */}
        <header
          className={`
            sticky top-0 z-30 h-14 flex items-center gap-4 px-4 lg:px-6
            transition-all duration-200
            ${scrolled ? 'glass-panel shadow-sm' : 'bg-transparent'}
          `}
        >
          <button
            className="lg:hidden p-2 -ml-2"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5 text-slate-600" />
          </button>
          <div className="flex-1" />
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
            <Sparkles className="w-3.5 h-3.5 text-ai-500" />
            <span>5个AI Agent 在线</span>
          </div>
        </header>

        {/* Page content */}
        <div className="p-4 lg:p-6 max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/exam" element={<Exam />} />
            <Route path="/practice" element={<Practice />} />
            <Route path="/ai-summary" element={<AISummary />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/knowledge" element={<KnowledgeMap />} />
            <Route path="/flashcards" element={<FlashcardsPage />} />
          </Routes>
        </div>
      </main>

      {/* Global RAG Chat Widget - available on all pages */}
      <ChatWidget />
    </div>
  )
}
