"""
Question service - loads and manages questions.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
QUESTIONS_PATH = BASE_DIR / "questions" / "questions.json"

_questions_cache: Optional[List[Dict[str, Any]]] = None
_questions_by_id: Optional[Dict[int, Dict[str, Any]]] = None


def _build_questions_index(questions: List[Dict]) -> Dict[int, Dict]:
    by_id: Dict[int, Dict] = {}
    for q in questions:
        by_id[q["id"]] = q
    return by_id


def load_questions() -> List[Dict[str, Any]]:
    """Load all questions from JSON file."""
    global _questions_cache
    if _questions_cache is None:
        with open(QUESTIONS_PATH, encoding="utf-8") as f:
            _questions_cache = json.load(f)
    return _questions_cache


def get_question_by_id(qid: int) -> Optional[Dict[str, Any]]:
    """Get a question by ID."""
    if _questions_by_id is None:
        load_questions()
    return _questions_by_id.get(qid) if _questions_by_id else None


def get_questions_by_type(qtype: str) -> List[Dict[str, Any]]:
    """Get questions filtered by type."""
    questions = load_questions()
    return [q for q in questions if q["type"] == qtype]


def get_questions_batch(
    qtype: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get a paginated batch of questions."""
    questions = load_questions()
    if qtype:
        questions = [q for q in questions if q["type"] == qtype]
    return questions[offset:offset + limit]


def get_stats() -> Dict[str, Any]:
    """Get question statistics."""
    questions = load_questions()
    stats = {
        "total": len(questions),
        "by_type": {},
        "single": len([q for q in questions if q["type"] == "single"]),
        "multiple": len([q for q in questions if q["type"] == "multiple"]),
        "truefalse": len([q for q in questions if q["type"] == "truefalse"]),
    }
    return stats
