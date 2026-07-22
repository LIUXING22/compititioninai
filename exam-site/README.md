# AI 训练师初赛理论题库 - 智能答题平台

基于 **Multi-Agent AI 技术** 的全栈智能答题与学习分析平台，用于深圳市第十六届职工技术创新运动会——人工智能训练师职业技能竞赛初赛理论题库（500题）的学习与备考。

## 技术架构

### 后端 (FastAPI)
- **框架**: FastAPI + Uvicorn
- **AI引擎**: 5个专业Agent协同工作的Multi-Agent系统
  - 🧠 **知识总结Agent** - 自动生成知识点总结、知识地图、知识卡片
  - 💡 **题目解析Agent** - 逐题详细解析，关联知识点
  - 📊 **学习分析Agent** - 多维度分析学习数据，识别薄弱点
  - 🎯 **考点预测Agent** - 基于题目分布预测高频考点
  - 📅 **学习规划Agent** - 制定个性化学习计划
- **服务**: 考试管理、练习模式、RESTful API

### 前端 (React + Vite + TypeScript + TailwindCSS)
- **框架**: React 18 + TypeScript + Vite 5
- **UI**: TailwindCSS 3 + Lucide React Icons
- **图表**: Recharts
- **路由**: React Router DOM v6

### 题库
- 500道题（已从PDF解析）
  - 单选题 300 题
  - 多选题 70 题
  - 判断题 130 题

## 快速开始

### 方式一：使用启动脚本 (Windows)

```bash
cd exam-site
start.bat
```

### 方式二：手动启动

#### 1. 启动后端

```bash
cd exam-site/backend

# 安装依赖
pip install -r requirements.txt

# 解析PDF题目（如果还没解析）
python questions/parse_pdf.py

# 启动服务
python run.py
# 或: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

AI 错题解释默认提供本地降级解析。要启用 OpenAI 云端解释，请复制
`backend/.env.example` 为 `backend/.env`，并配置：

```dotenv
OPENAI_API_KEY=你的_API_Key
OPENAI_MODEL=gpt-5-mini
OPENAI_TIMEOUT_SECONDS=15
```

API Key 仅由后端读取，不要写入前端环境变量或提交到版本库。可通过
`GET /api/ai/status` 查看当前是否启用了云端解释。

后端服务地址: http://localhost:8000
API文档: http://localhost:8000/docs

#### 2. 启动前端

```bash
cd exam-site/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端地址: http://localhost:5173

## 项目结构

```
exam-site/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI主应用
│   │   ├── agents/
│   │   │   └── multi_agent.py   # Multi-Agent AI系统
│   │   ├── services/
│   │   │   ├── question_service.py  # 题目服务
│   │   │   └── exam_service.py      # 考试服务
│   │   └── config/
│   │       └── agents.json      # Agent配置
│   ├── questions/
│   │   ├── questions.json       # 500道题（结构化JSON）
│   │   └── parse_pdf.py         # PDF解析脚本
│   ├── requirements.txt
│   └── run.py                   # 服务启动入口
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx         # 首页/仪表盘
│   │   │   ├── Exam.tsx         # 模拟考试
│   │   │   ├── Practice.tsx     # 练习模式
│   │   │   ├── AISummary.tsx    # AI智能总结
│   │   │   ├── Analytics.tsx    # 学习分析
│   │   │   ├── KnowledgeMap.tsx # 知识地图
│   │   │   └── Flashcards.tsx   # 知识卡片
│   │   ├── lib/
│   │   │   └── api.ts           # API客户端
│   │   ├── types/
│   │   │   └── index.ts         # TypeScript类型
│   │   ├── App.tsx              # 主应用（含路由）
│   │   └── main.tsx             # 入口
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
│
└── start.bat                    # Windows一键启动
```

## API接口

### 题目相关
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/questions/stats | 题目统计 |
| GET | /api/questions | 获取题目列表 |
| GET | /api/questions/{id} | 获取单题 |
| GET | /api/search?q=keyword | 搜索题目 |

### 考试相关
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/exam/create | 创建考试 |
| POST | /api/exam/{id}/answer | 提交答案 |
| POST | /api/exam/{id}/complete | 完成考试 |
| GET | /api/exam/{id}/result | 考试结果 |

### AI Multi-Agent
| 方法 | 路径 | Agent | 功能 |
|------|------|-------|------|
| POST | /api/ai/summarize | Summarizer | 知识总结 |
| POST | /api/ai/explain | Explainer | 题目解析 |
| POST | /api/ai/analyze | Analyzer | 学习分析 |
| POST | /api/ai/predict | Predictor | 考点预测 |
| POST | /api/ai/plan | Planner | 学习计划 |
| POST | /api/ai/full-analysis | All | 全部分析 |
| POST | /api/ai/study-materials | All | 学习资料生成 |
| POST | /api/ai/exam-help | Explainer | 考试辅助 |

## 功能特性

### 📝 模拟考试
- 仿真考试环境（50题/60分钟）
- 实时倒计时
- 自动计时和评分
- 答题卡导航
- 完成后详细成绩报告

### 📚 练习模式
- 5种练习模式
- 顺序练习 / 随机练习
- 按题型专项练习
- 即时反馈和回顾

### 🤖 AI 智能总结
- **知识总结**: 按知识点分类总结
- **知识点分析**: 各知识点占比可视化
- **知识地图**: 层级化知识结构
- **知识卡片**: 翻转卡片记忆

### 📊 学习分析
- 正确率趋势图
- 知识掌握度雷达图
- 题型表现分析
- 薄弱点识别
- AI个性化建议

### 🎯 考点预测
- 高频考点排行
- 重点题目推荐
- AI复习计划

### 🗺️ 知识地图
- 可视化知识结构
- 层级化展示
- 题目数量统计

### 🎴 知识卡片
- 翻转卡片记忆
- 按题型筛选
- 键盘快捷键支持

## Multi-Agent 系统

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Summarizer │────▶│  Analyzer   │────▶│  Predictor  │────▶│   Planner   │
│  总结Agent   │     │  分析Agent   │     │  预测Agent   │     │  规划Agent   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
        ▲                   ▲                   ▲                   ▲
        │                   │                   │                   │
        └───────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │   协调器Agent    │
                    └─────────────────┘
```

## 环境要求

- Python >= 3.9
- Node.js >= 18
- npm >= 9

## 开发

### 后端开发
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

## 部署

### 生产环境
```bash
# 构建前端
cd frontend
npm run build

# 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 许可证

MIT
