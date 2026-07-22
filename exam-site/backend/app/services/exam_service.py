"""
Exam service - manages exam sessions, scoring, and results.
"""
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.services.question_service import (
    get_questions_by_type,
    get_question_by_id,
    get_questions_batch,
    load_questions,
)


@dataclass
class ExamConfig:
    """Configuration for an exam session."""
    total_questions: int = 50
    single_ratio: float = 0.6
    multiple_ratio: float = 0.15
    truefalse_ratio: float = 0.25
    time_limit_minutes: int = 60
    shuffle: bool = True
    show_result_immediately: bool = True
    single_score: float = 1.0
    multiple_score: float = 2.0
    truefalse_score: float = 1.0
    multiple_penalty: float = 0.5  # Penalty per wrong option in multi-choice


@dataclass
class ExamQuestion:
    """A question in an exam session."""
    question_id: int
    order: int
    question: Dict[str, Any]
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    time_spent_ms: int = 0
    answered_at: Optional[str] = None


@dataclass
class ExamSession:
    """An active exam session."""
    session_id: str
    config: ExamConfig
    questions: List[ExamQuestion] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    submitted_at: Optional[str] = None
    completed: bool = False
    score: float = 0.0
    max_score: float = 0.0
    correct_count: int = 0
    total_count: int = 0


# In-memory session store (use Redis in production)
_sessions: Dict[str, ExamSession] = {}


def create_exam_session(
    session_id: str,
    config: Optional[ExamConfig] = None,
) -> ExamSession:
    """Create a new exam session with selected questions."""
    if config is None:
        config = ExamConfig()

    all_questions = load_questions()
    singles = [q for q in all_questions if q["type"] == "single"]
    multiples = [q for q in all_questions if q["type"] == "multiple"]
    truefalses = [q for q in all_questions if q["type"] == "truefalse"]

    # Calculate count per type
    total = config.total_questions
    single_count = max(1, int(total * config.single_ratio))
    multiple_count = max(1, int(total * config.multiple_ratio))
    truefalse_count = max(1, total - single_count - multiple_count)

    # Ensure we don't exceed available questions
    single_count = min(single_count, len(singles))
    multiple_count = min(multiple_count, len(multiples))
    truefalse_count = min(truefalse_count, len(truefalses))

    selected_questions = []

    # Random selection
    if config.shuffle:
        random.seed(hash(session_id) % (2**32))
        selected = random.sample(singles, min(single_count, len(singles)))
        selected_questions.extend(selected)
        selected = random.sample(multiples, min(multiple_count, len(multiples)))
        selected_questions.extend(selected)
        selected = random.sample(truefalses, min(truefalse_count, len(truefalses)))
        selected_questions.extend(selected)
    else:
        selected_questions.extend(singles[:single_count])
        selected_questions.extend(multiples[:multiple_count])
        selected_questions.extend(truefalses[:truefalse_count])

    # Shuffle order
    if config.shuffle:
        random.shuffle(selected_questions)

    # Build exam questions
    exam_questions = []
    for i, q in enumerate(selected_questions):
        exam_questions.append(ExamQuestion(
            question_id=q["id"],
            order=i + 1,
            question=q,
        ))

    # Calculate max score
    max_score = (
        single_count * config.single_score +
        multiple_count * config.multiple_score +
        truefalse_count * config.truefalse_score
    )

    session = ExamSession(
        session_id=session_id,
        config=config,
        questions=exam_questions,
        max_score=max_score,
        total_count=len(exam_questions),
    )

    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[ExamSession]:
    """Get an existing exam session."""
    return _sessions.get(session_id)


def submit_answer(
    session_id: str,
    question_id: int,
    answer: str,
    time_spent_ms: int = 0,
) -> Optional[Dict[str, Any]]:
    """Submit an answer for a question in an exam."""
    session = _sessions.get(session_id)
    if not session:
        return None

    for eq in session.questions:
        if eq.question_id == question_id:
            eq.user_answer = answer
            eq.time_spent_ms = time_spent_ms
            eq.answered_at = datetime.now().isoformat()

            q = eq.question
            correct_answer = q["answer"]

            if q["type"] == "multiple":
                user_set = set(answer)
                correct_set = set(correct_answer)
                eq.is_correct = user_set == correct_set
            else:
                eq.is_correct = answer == correct_answer

            return {
                "is_correct": eq.is_correct,
                "correct_answer": correct_answer,
                "question_id": question_id,
            }

    return None


def complete_exam(session_id: str) -> Optional[Dict[str, Any]]:
    """Complete an exam and calculate final score."""
    session = _sessions.get(session_id)
    if not session:
        return None

    session.completed = True
    session.submitted_at = datetime.now().isoformat()

    score = 0.0
    correct = 0

    for eq in session.questions:
        if eq.is_correct is None:
            eq.is_correct = False  # Unanswered = wrong

        if eq.is_correct:
            correct += 1
            if eq.question["type"] == "single":
                score += session.config.single_score
            elif eq.question["type"] == "multiple":
                score += session.config.multiple_score
            elif eq.question["type"] == "truefalse":
                score += session.config.truefalse_score

    session.score = score
    session.correct_count = correct

    rate = correct / session.total_count * 100 if session.total_count else 0

    return get_exam_result(session)


def get_exam_result(session: ExamSession) -> Dict[str, Any]:
    """Get the result of a completed exam."""
    rate = session.correct_count / session.total_count * 100 if session.total_count else 0

    # Build question results
    question_results = []
    for eq in session.questions:
        question_results.append({
            "id": eq.question_id,
            "order": eq.order,
            "type": eq.question["type"],
            "question": eq.question["question"],
            "options": eq.question["options"],
            "user_answer": eq.user_answer,
            "correct_answer": eq.question["answer"],
            "is_correct": eq.is_correct,
            "time_spent_ms": eq.time_spent_ms,
        })

    # Type breakdown
    type_stats = {}
    for eq in session.questions:
        qtype = eq.question["type"]
        if qtype not in type_stats:
            type_stats[qtype] = {"total": 0, "correct": 0}
        type_stats[qtype]["total"] += 1
        if eq.is_correct:
            type_stats[qtype]["correct"] += 1

    # Calculate time
    if session.submitted_at:
        try:
            start = datetime.fromisoformat(session.started_at)
            end = datetime.fromisoformat(session.submitted_at)
            elapsed_seconds = (end - start).total_seconds()
        except Exception:
            elapsed_seconds = 0
    else:
        elapsed_seconds = 0

    return {
        "session_id": session.session_id,
        "completed": session.completed,
        "score": {
            "raw": round(session.score, 1),
            "max": round(session.max_score, 1),
            "percentage": round(rate, 1),
            "grade": _score_to_grade(rate),
        },
        "summary": {
            "total": session.total_count,
            "correct": session.correct_count,
            "incorrect": session.total_count - session.correct_count,
            "time_seconds": round(elapsed_seconds, 1),
        },
        "by_type": {
            k: {
                "total": v["total"],
                "correct": v["correct"],
                "rate": round(v["correct"] / v["total"] * 100, 1) if v["total"] else 0,
            }
            for k, v in type_stats.items()
        },
        "questions": question_results,
        "started_at": session.started_at,
        "submitted_at": session.submitted_at,
    }


def get_exam_progress(session_id: str) -> Optional[Dict[str, Any]]:
    """Get current exam progress."""
    session = _sessions.get(session_id)
    if not session:
        return None

    answered = sum(1 for eq in session.questions if eq.user_answer is not None)
    correct = sum(1 for eq in session.questions if eq.is_correct)

    return {
        "session_id": session_id,
        "total": session.total_count,
        "answered": answered,
        "remaining": session.total_count - answered,
        "current_correct": correct,
        "progress_percentage": round(answered / session.total_count * 100, 1) if session.total_count else 0,
    }


def delete_session(session_id: str) -> bool:
    """Delete an exam session."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def get_wrong_questions(session_id: str) -> List[Dict]:
    """Get all wrong questions from an exam."""
    session = _sessions.get(session_id)
    if not session:
        return []

    return [
        {
            "id": eq.question_id,
            "type": eq.question["type"],
            "question": eq.question["question"],
            "options": eq.question["options"],
            "correct_answer": eq.question["answer"],
            "user_answer": eq.user_answer,
        }
        for eq in session.questions
        if not eq.is_correct
    ]


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
