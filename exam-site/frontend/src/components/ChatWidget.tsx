import { useState, useRef, useEffect } from 'react';
import {
  MessageCircle,
  X,
  Send,
  Loader2,
  Bot,
  User,
  FileText,
  ExternalLink,
  AlertCircle,
} from 'lucide-react';
import {
  sendChatMessage,
  getChatSources,
  type ChatMessage,
  type ChatSource,
  type ChatResponse,
} from '../lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
  error?: string;
}

const WELCOME_MESSAGE: Message = {
  role: 'assistant',
  content: '你好！我是AI训练师备考智能助教。\n\n我可以帮你：\n• 解答题库中的任何题目\n• 解释知识点和概念\n• 分析模考试卷中的错题\n• 提供备考建议\n\n尽管问我吧！',
};

const SUGGESTED_QUESTIONS = [
  '强化学习有哪些求解方式？',
  '什么是工匠精神？',
  '计算机网络的性能指标有哪些？',
  'Python中列表和字典的区别是什么？',
];

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user';
  const [showSources, setShowSources] = useState(false);

  return (
    <div className={`flex gap-2.5 mb-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
          isUser
            ? 'bg-primary-100 text-primary-600'
            : 'bg-gradient-to-br from-primary-500 to-ai-500 text-white'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble */}
      <div className={`flex-1 min-w-0 ${isUser ? 'flex flex-col items-end' : ''}`}>
        <div
          className={`max-w-[90%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? 'bg-primary-500 text-white rounded-tr-md'
              : msg.error
              ? 'bg-red-50 text-red-700 border border-red-200 rounded-tl-md'
              : 'bg-slate-100 text-slate-700 rounded-tl-md'
          }`}
        >
          {msg.isStreaming && !msg.content ? (
            <div className="flex gap-1.5 py-1">
              <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          ) : (
            msg.content || (msg.error ? msg.error : '...')
          )}
        </div>

        {/* Sources */}
        {msg.sources && msg.sources.length > 0 && (
          <div className={`mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            <button
              onClick={() => setShowSources(!showSources)}
              className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-primary-500 transition-colors"
            >
              <FileText className="w-3 h-3" />
              参考了 {msg.sources.length} 个文档片段
            </button>
            {showSources && (
              <div className={`mt-2 space-y-1.5 max-w-[85%] ${isUser ? 'ml-auto' : ''}`}>
                {msg.sources.map((src, i) => (
                  <div
                    key={i}
                    className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-600 shadow-sm"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-primary-600 text-[10px] uppercase">
                        {src.source}
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {Math.round(src.relevance * 100)}% 匹配
                      </span>
                    </div>
                    <div className="line-clamp-2 text-slate-500">{src.excerpt}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Error retry */}
        {msg.error && (
          <button
            className="text-xs text-primary-500 mt-1 hover:underline"
            onClick={() => window.location.reload()}
          >
            点击重试
          </button>
        )}
      </div>
    </div>
  );
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  const handleSend = async (text?: string) => {
    const msgText = text || input.trim();
    if (!msgText || loading) return;

    const userMsg: Message = { role: 'user', content: msgText };
    const streamingMsg: Message = { role: 'assistant', content: '', isStreaming: true };

    setMessages((prev) => [...prev, userMsg, streamingMsg]);
    setInput('');
    setLoading(true);

    try {
      // Build history from messages
      const history: ChatMessage[] = messages
        .filter((m) => !m.isStreaming && !m.error)
        .map((m) => ({ role: m.role, content: m.content }));

      const result: ChatResponse = await sendChatMessage(msgText, history);

      // Replace streaming placeholder with actual response
      setMessages((prev) => {
        const newMsgs = [...prev];
        const lastIdx = newMsgs.length - 1;
        newMsgs[lastIdx] = {
          role: 'assistant',
          content: result.reply || '（无响应）',
          sources: result.sources || [],
          error: result.error,
        };
        return newMsgs;
      });
    } catch (e: any) {
      setMessages((prev) => {
        const newMsgs = [...prev];
        const lastIdx = newMsgs.length - 1;
        newMsgs[lastIdx] = {
          role: 'assistant',
          content: '抱歉，AI服务暂时不可用。请检查网络连接后重试。',
          error: e?.message || '请求失败',
        };
        return newMsgs;
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating Button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-ai-500 text-white shadow-2xl hover:scale-110 transition-all flex items-center justify-center group"
          title="AI 智能助教"
        >
          <MessageCircle className="w-6 h-6 group-hover:rotate-12 transition-transform" />
          <span className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-amber-400 border-2 border-white flex items-center justify-center">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
          </span>
        </button>
      )}

      {/* Chat Panel */}
      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-[400px] h-[600px] max-h-[80vh] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-4">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-100 bg-gradient-to-r from-primary-50 to-ai-50">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-600 to-ai-500 flex items-center justify-center shadow">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="font-semibold text-sm text-slate-800">AI 智能助教</div>
                <div className="text-[10px] text-slate-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                  RAG 文档问答
                </div>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 scrollbar-thin">
            {messages.map((msg, i) => (
              <MessageBubble key={i} msg={msg} />
            ))}

            {/* Suggested questions */}
            {messages.length === 1 && !loading && (
              <div className="mt-2 space-y-1.5">
                <div className="text-[10px] text-slate-400 mb-2">你可以试着问：</div>
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="block w-full text-left px-3 py-2 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-600 hover:border-primary-200 hover:bg-primary-50 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="px-4 py-3 border-t border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入问题，回车发送..."
                disabled={loading}
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100 disabled:opacity-50 transition-all"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="btn-primary !p-2.5 !rounded-xl shrink-0"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
