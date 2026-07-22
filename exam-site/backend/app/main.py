"""
FastAPI main application for the AI Training Quiz Platform.
Multi-agent AI system for intelligent learning assistance.
"""
import asyncio
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.multi_agent import (
    AgentOrchestrator,
    get_orchestrator,
)
from app.services.exam_service import (
    ExamConfig,
    complete_exam,
    create_exam_session,
    delete_session,
    get_exam_progress,
    get_exam_result,
    get_session,
    get_wrong_questions,
    submit_answer,
)
from app.services.question_service import (
    get_questions_by_type,
    get_question_by_id,
    get_questions_batch,
    get_stats,
    load_questions,
)
from app.services.ai_explanation_service import (
    explain_wrong_answer,
    get_ai_explanation_status,
)


# ── Lifecycle ──────────────────────────────────────────────────────────────

orchestrator_instance: Optional[AgentOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    global orchestrator_instance
    orchestrator_instance = AgentOrchestrator()
    yield
    orchestrator_instance = None


# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI 训练师初赛题库 - 智能答题平台",
    description="基于 Multi-Agent AI 技术的智能答题与学习分析平台",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "agents": orchestrator_instance.list_agents() if orchestrator_instance else [],
    }


# ── Question Endpoints ─────────────────────────────────────────────────────

@app.get("/api/questions/stats")
async def get_question_stats():
    """Get question statistics."""
    return get_stats()


@app.get("/api/questions")
async def list_questions(
    type: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    keyword: Optional[str] = None,
):
    """List questions with optional filtering."""
    questions = get_questions_batch(qtype=type, offset=offset, limit=limit)

    if keyword:
        keyword_lower = keyword.lower()
        questions = [
            q for q in questions
            if keyword_lower in q["question"].lower()
            or any(keyword_lower in str(v).lower() for v in q.get("options", {}).values())
        ]

    total = get_stats()["total"]
    if type:
        total = len(get_questions_by_type(type))

    return {
        "questions": questions,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(questions) < total,
    }


@app.get("/api/questions/{question_id}")
async def get_question(question_id: int):
    """Get a specific question by ID."""
    q = get_question_by_id(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


@app.get("/api/questions/type/{qtype}")
async def get_questions_by_type_endpoint(
    qtype: str,
    offset: int = 0,
    limit: int = 50,
):
    """Get questions by type (single, multiple, truefalse)."""
    questions = get_questions_by_type(qtype)
    result = questions[offset:offset + limit]
    return {
        "questions": result,
        "total": len(questions),
        "type": qtype,
        "offset": offset,
        "limit": limit,
    }


# ── Exam Endpoints ─────────────────────────────────────────────────────────

@app.post("/api/exam/create")
async def create_exam(config: Optional[Dict[str, Any]] = None):
    """Create a new exam session."""
    if config:
        cfg = ExamConfig(
            total_questions=config.get("total_questions", 50),
            time_limit_minutes=config.get("time_limit_minutes", 60),
        )
    else:
        cfg = ExamConfig()

    session_id = f"exam_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    session = create_exam_session(session_id, cfg)

    return {
        "session_id": session_id,
        "config": {
            "total_questions": session.config.total_questions,
            "time_limit_minutes": session.config.time_limit_minutes,
            "single_score": session.config.single_score,
            "multiple_score": session.config.multiple_score,
            "truefalse_score": session.config.truefalse_score,
            "multiple_penalty": session.config.multiple_penalty,
        },
        "questions": [
            {
                "order": eq.order,
                "id": eq.question_id,
                "type": eq.question["type"],
                "question": eq.question["question"],
                "options": eq.question["options"],
            }
            for eq in session.questions
        ],
        "total": session.total_count,
        "started_at": session.started_at,
    }


@app.post("/api/exam/{session_id}/answer")
async def submit_exam_answer(session_id: str, body: Dict[str, Any]):
    """Submit an answer for a question."""
    question_id = body.get("question_id")
    answer = body.get("answer", "")
    time_spent = body.get("time_spent_ms", 0)

    if question_id is None:
        raise HTTPException(status_code=400, detail="question_id required")

    result = submit_answer(session_id, question_id, answer, time_spent)
    if result is None:
        raise HTTPException(status_code=404, detail="Session or question not found")

    return result


@app.post("/api/exam/{session_id}/complete")
async def complete_exam_session(session_id: str):
    """Complete the exam and get results."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = complete_exam(session_id)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to complete exam")

    return result


@app.get("/api/exam/{session_id}/progress")
async def get_exam_progress_endpoint(session_id: str):
    """Get exam progress."""
    progress = get_exam_progress(session_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return progress


@app.get("/api/exam/{session_id}/result")
async def get_exam_result_endpoint(session_id: str):
    """Get exam result."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = get_exam_result(session)
    return result


@app.get("/api/exam/{session_id}/wrong")
async def get_exam_wrong(session_id: str):
    """Get wrong questions from an exam."""
    wrong = get_wrong_questions(session_id)
    return {
        "session_id": session_id,
        "wrong_count": len(wrong),
        "wrong_questions": wrong,
    }


@app.delete("/api/exam/{session_id}")
async def delete_exam_session(session_id: str):
    """Delete an exam session."""
    success = delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}


# ── Practice Endpoints ──────────────────────────────────────────────────────

@app.get("/api/practice/mode")
async def get_practice_modes():
    """Get available practice modes."""
    return {
        "modes": [
            {"id": "sequential", "name": "顺序练习", "desc": "按题号顺序答题"},
            {"id": "random", "name": "随机练习", "desc": "随机选题答题"},
            {"id": "by_type_single", "name": "单选题专练", "desc": "只练习单选题"},
            {"id": "by_type_multiple", "name": "多选题专练", "desc": "只练习多选题"},
            {"id": "by_type_truefalse", "name": "判断题专练", "desc": "只练习判断题"},
            {"id": "wrong_only", "name": "错题重练", "desc": "只练习做错的题"},
            {"id": "flashcard", "name": "知识卡片", "desc": "翻转卡片记忆"},
        ]
    }


@app.post("/api/practice/start")
async def start_practice(body: Dict[str, Any]):
    """Start a practice session."""
    mode = body.get("mode", "random")
    count = max(1, min(int(body.get("count", 20)), 500))
    qtypes = body.get("types", ["single", "multiple", "truefalse"])

    questions = load_questions()
    filtered = [q for q in questions if q["type"] in qtypes]

    if mode == "sequential":
        selected = filtered[:count]
    elif mode == "random":
        random.seed()
        selected = random.sample(filtered, min(count, len(filtered)))
    else:
        selected = filtered[:count]

    return {
        "questions": selected,
        "total": len(selected),
        "mode": mode,
    }


# ── AI Multi-Agent Endpoints ────────────────────────────────────────────────

@app.get("/api/ai/agents")
async def list_agents():
    """List all available AI agents."""
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")
    return {
        "agents": orchestrator_instance.list_agents(),
        "total": len(orchestrator_instance.agents),
    }


@app.get("/api/ai/status")
async def ai_status():
    """Report whether remote AI explanations are configured."""
    return get_ai_explanation_status()


@app.post("/api/ai/summarize")
async def ai_summarize(body: Dict[str, Any]):
    """
    Generate knowledge summary using the Summarizer Agent.
    Modes: full_summary, chapter_summary, knowledge_cards, knowledge_map, topic_analysis
    """
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    questions = body.get("questions", load_questions())
    mode = body.get("mode", "full_summary")

    result = await orchestrator_instance.execute_single(
        "summarizer",
        {"questions": questions, "mode": mode},
    )
    return {
        "agent": "summarizer",
        "mode": mode,
        "success": result.success,
        "data": result.data,
        "execution_time_ms": result.execution_time_ms,
    }


@app.post("/api/ai/explain")
async def ai_explain(body: Dict[str, Any]):
    """
    Explain a wrong answer with OpenAI and a deterministic local fallback.
    """
    question = body.get("question")
    user_answer = body.get("user_answer", "")

    if not question:
        raise HTTPException(status_code=400, detail="question required")
    if not question.get("answer"):
        raise HTTPException(status_code=400, detail="question answer required")

    result = await explain_wrong_answer(question, user_answer)
    return {
        "agent": "openai_explainer" if result["data"]["source"] == "openai" else "local_explainer",
        **result,
    }


@app.post("/api/ai/analyze")
async def ai_analyze(body: Dict[str, Any]):
    """
    Analyze learning progress using the Analyzer Agent.
    Modes: full_analysis, weak_points, progress_report, mastery_map
    """
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    exam_records = body.get("exam_records", [])
    mode = body.get("mode", "full_analysis")

    result = await orchestrator_instance.execute_single(
        "analyzer",
        {
            "exam_records": exam_records,
            "questions": {q["id"]: q for q in load_questions()},
            "mode": mode,
        },
    )
    return {
        "agent": "analyzer",
        "mode": mode,
        "success": result.success,
        "data": result.data,
        "execution_time_ms": result.execution_time_ms,
    }


@app.post("/api/ai/predict")
async def ai_predict(body: Dict[str, Any]):
    """
    Predict exam points using the Predictor Agent.
    Modes: full_prediction, high_frequency, key_points, review_plan
    """
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    questions = body.get("questions", load_questions())
    mode = body.get("mode", "full_prediction")

    result = await orchestrator_instance.execute_single(
        "predictor",
        {"questions": questions, "mode": mode},
    )
    return {
        "agent": "predictor",
        "mode": mode,
        "success": result.success,
        "data": result.data,
        "execution_time_ms": result.execution_time_ms,
    }


@app.post("/api/ai/plan")
async def ai_plan(body: Dict[str, Any]):
    """
    Create a study plan using the Planner Agent.
    Plan types: exam_prep, streak_recovery, custom
    """
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    plan_type = body.get("plan_type", "exam_prep")
    exam_date = body.get("exam_date", "")
    daily_minutes = body.get("daily_minutes", 30)
    current_level = body.get("current_level", "beginner")

    result = await orchestrator_instance.execute_single(
        "planner",
        {
            "plan_type": plan_type,
            "exam_date": exam_date,
            "daily_minutes": daily_minutes,
            "current_level": current_level,
        },
    )
    return {
        "agent": "planner",
        "plan_type": plan_type,
        "success": result.success,
        "data": result.data,
        "execution_time_ms": result.execution_time_ms,
    }


@app.post("/api/ai/full-analysis")
async def ai_full_analysis(body: Dict[str, Any]):
    """
    Run full AI analysis pipeline:
    Summarizer -> Analyzer -> Predictor -> Planner
    """
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    questions = body.get("questions", load_questions())
    exam_records = body.get("exam_records", [])

    start = time.perf_counter()
    result = await orchestrator_instance.execute_full_analysis({
        "questions": questions,
        "exam_records": exam_records,
    })
    total_ms = (time.perf_counter() - start) * 1000

    return {
        **result,
        "total_ms": round(total_ms, 1),
    }


@app.post("/api/ai/study-materials")
async def ai_study_materials():
    """
    Generate complete study materials using all agents in parallel.
    """
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    questions = load_questions()
    result = await orchestrator_instance.generate_study_materials(questions)
    return result


@app.post("/api/ai/exam-help")
async def ai_exam_help(body: Dict[str, Any]):
    """
    Get AI help for a specific exam question.
    Returns explanation and knowledge context.
    """
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    question = body.get("question")
    user_answer = body.get("user_answer", "")

    if not question:
        raise HTTPException(status_code=400, detail="question required")

    result = await orchestrator_instance.execute_exam_help(question, user_answer)
    return result


# ── Knowledge Card Endpoints ────────────────────────────────────────────────

@app.get("/api/knowledge/cards")
async def get_knowledge_cards(type_filter: Optional[str] = None):
    """Get flashcards for study."""
    questions = load_questions()
    if type_filter:
        questions = [q for q in questions if q["type"] == type_filter]

    cards = []
    for q in questions:
        if q["type"] == "truefalse":
            cards.append({
                "id": q["id"],
                "front": q["question"],
                "back": "正确" if q["answer"] == "A" else "错误",
                "type": "truefalse",
            })
        else:
            correct_texts = [q["options"][k] for k in q["answer"] if k in q["options"]]
            cards.append({
                "id": q["id"],
                "front": q["question"],
                "back": " | ".join(correct_texts),
                "type": q["type"],
            })

    return {"cards": cards[:100], "total": len(cards)}


@app.get("/api/knowledge/map")
async def get_knowledge_map():
    """Get knowledge map data."""
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    result = await orchestrator_instance.execute_single(
        "summarizer",
        {"questions": load_questions(), "mode": "knowledge_map"},
    )
    return {
        "success": result.success,
        "data": result.data,
        "execution_time_ms": result.execution_time_ms,
    }


# ── Random Quiz / Quick Test ────────────────────────────────────────────────

@app.post("/api/quiz/random")
async def create_random_quiz(body: Dict[str, Any]):
    """Create a random quiz with specified parameters."""
    count = min(body.get("count", 20), 100)
    types = body.get("types", ["single", "multiple", "truefalse"])
    difficulty = body.get("difficulty", "mixed")

    questions = load_questions()
    filtered = [q for q in questions if q["type"] in types]

    random.seed()
    selected = random.sample(filtered, min(count, len(filtered)))

    return {
        "quiz_id": f"quiz_{int(time.time())}",
        "questions": [
            {
                "id": q["id"],
                "type": q["type"],
                "question": q["question"],
                "options": q["options"],
            }
            for q in selected
        ],
        "total": len(selected),
    }


@app.post("/api/quiz/{quiz_id}/grade")
async def grade_quiz(quiz_id: str, body: Dict[str, Any]):
    """Grade a quiz submission."""
    answers = body.get("answers", {})
    questions_map = {q["id"]: q for q in load_questions()}

    correct = 0
    total = len(answers)
    results = []

    for qid_str, user_ans in answers.items():
        qid = int(qid_str)
        q = questions_map.get(qid)
        if not q:
            continue

        if q["type"] == "multiple":
            is_correct = set(user_ans) == set(q["answer"])
        else:
            is_correct = user_ans == q["answer"]

        if is_correct:
            correct += 1

        results.append({
            "id": qid,
            "user_answer": user_ans,
            "correct_answer": q["answer"],
            "is_correct": is_correct,
            "question": q["question"],
        })

    return {
        "quiz_id": quiz_id,
        "total": total,
        "correct": correct,
        "incorrect": total - correct,
        "score_percentage": round(correct / total * 100, 1) if total else 0,
        "grade": _score_to_grade(correct / total * 100 if total else 0),
        "results": results,
    }


# ── Search ──────────────────────────────────────────────────────────────────

@app.get("/api/search")
async def search_questions(q: str, limit: int = 20):
    """Search questions by keyword."""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query too short (min 2 chars)")

    q_lower = q.lower()
    questions = load_questions()

    results = []
    for question in questions:
        score = 0
        if q_lower in question["question"].lower():
            score += 2
        for opt_val in question.get("options", {}).values():
            if q_lower in opt_val.lower():
                score += 1

        if score > 0:
            results.append({
                "id": question["id"],
                "type": question["type"],
                "question": question["question"],
                "options": question["options"],
                "answer": question["answer"],
                "relevance_score": score,
            })

    results.sort(key=lambda x: -x["relevance_score"])
    return {
        "query": q,
        "results": results[:limit],
        "total": len(results),
    }


# ── Analytics Dashboard ─────────────────────────────────────────────────────

@app.post("/api/analytics/dashboard")
async def get_analytics_dashboard(body: Dict[str, Any]):
    """Get comprehensive analytics dashboard data."""
    if not orchestrator_instance:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    exam_records = body.get("exam_records", [])
    questions = {q["id"]: q for q in load_questions()}

    # Run analyzer
    analysis_result = await orchestrator_instance.execute_single(
        "analyzer",
        {
            "exam_records": exam_records,
            "questions": questions,
            "mode": "full_analysis",
        },
    )

    # Run predictor for recommendation
    prediction_result = await orchestrator_instance.execute_single(
        "predictor",
        {"questions": list(questions.values()), "mode": "high_frequency"},
    )

    # Run summarizer for overview
    summary_result = await orchestrator_instance.execute_single(
        "summarizer",
        {"questions": list(questions.values()), "mode": "topic_analysis"},
    )

    return {
        "analysis": analysis_result.data if analysis_result.success else {},
        "prediction": prediction_result.data if prediction_result.success else {},
        "topic_distribution": summary_result.data if summary_result.success else {},
        "generated_at": datetime.now().isoformat(),
    }


# ── Helper ──────────────────────────────────────────────────────────────────

def _score_to_grade(rate: float) -> str:
    if rate >= 90:
        return "优秀"
    elif rate >= 75:
        return "良好"
    elif rate >= 60:
        return "及格"
    elif rate > 0:
        return "不及格"
    return "未作答"
