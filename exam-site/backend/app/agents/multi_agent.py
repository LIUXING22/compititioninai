"""
Multi-Agent System for AI Training Platform.
Five specialized AI agents working together for intelligent learning.
"""
import asyncio
import json
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

import httpx


class AgentType(Enum):
    SUMMARIZER = "summarizer"
    EXPLAINER = "explainer"
    ANALYZER = "analyzer"
    PREDICTOR = "predictor"
    PLANNER = "planner"


@dataclass
class Message:
    """Inter-agent communication message."""
    sender: str
    receiver: str
    content: Any
    msg_type: str = "request"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent: str
    success: bool
    data: Any
    metadata: Dict = field(default_factory=dict)
    execution_time_ms: float = 0.0


class BaseAgent:
    """Base class for all AI agents."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.history: List[Message] = []
        self.capabilities: List[str] = []

    async def execute(self, context: Dict) -> AgentResult:
        """Execute the agent's main logic. Override in subclasses."""
        start = time.perf_counter()
        try:
            result = await self._run(context)
            elapsed = (time.perf_counter() - start) * 1000
            return AgentResult(
                agent=self.name,
                success=True,
                data=result,
                execution_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return AgentResult(
                agent=self.name,
                success=False,
                data={"error": str(e)},
                execution_time_ms=elapsed,
            )

    async def _run(self, context: Dict) -> Dict:
        raise NotImplementedError

    def send(self, receiver: str, content: Any, msg_type: str = "request"):
        msg = Message(
            sender=self.name, receiver=receiver,
            content=content, msg_type=msg_type,
        )
        self.history.append(msg)

    def receive(self, msg: Message):
        self.history.append(msg)


class KnowledgeSummarizerAgent(BaseAgent):
    """
    Summarizes knowledge from questions.
    Groups questions by topic, generates chapter summaries,
    creates knowledge cards.
    """

    def __init__(self):
        super().__init__("SummarizerAgent", "知识总结专家")
        self.capabilities = ["章节总结", "知识点归纳", "知识卡片生成", "知识地图构建"]

        # Topic keyword mapping for auto-classification
        self.topic_keywords: Dict[str, List[str]] = {
            "职业道德": ["道德", "诚信", "爱岗", "奉献", "工匠", "纪律", "遵纪", "守法"],
            "计算机基础": ["计算机", "硬件", "软件", "CPU", "内存", "操作系统", "二进制"],
            "网络技术": ["网络", "协议", "IP", "传输", "带宽", "路由器", "交换机"],
            "数据库": ["数据库", "SQL", "表", "查询", "数据", "清洗", "采集", "存储"],
            "Python编程": ["Python", "函数", "变量", "循环", "列表", "代码", "程序"],
            "机器学习": ["机器学习", "监督", "无监督", "训练", "模型", "算法", "特征"],
            "深度学习": ["深度学习", "神经网络", "CNN", "RNN", "卷积", "反向传播"],
            "强化学习": ["强化学习", "Q-Learning", "策略", "奖励", "智能体"],
            "自然语言处理": ["NLP", "自然语言", "分词", "词向量", "注意力"],
            "计算机视觉": ["视觉", "图像", "目标检测", "分割", "特征"],
            "数据采集": ["采集", "标注", "数据集", "标注", "传感器"],
            "AI产品": ["产品经理", "需求", "场景", "用户", "落地"],
            "大数据": ["大数据", "Hadoop", "Spark", "分布式"],
        }

    async def _run(self, context: Dict) -> Dict:
        questions = context.get("questions", [])
        mode = context.get("mode", "full_summary")

        if mode == "chapter_summary":
            return self._generate_chapter_summary(questions)
        elif mode == "knowledge_cards":
            return self._generate_knowledge_cards(questions)
        elif mode == "knowledge_map":
            return self._generate_knowledge_map(questions)
        elif mode == "topic_analysis":
            return self._analyze_by_topic(questions)
        else:
            return self._generate_full_summary(questions)

    def _classify_topic(self, question_text: str) -> str:
        for topic, keywords in self.topic_keywords.items():
            for kw in keywords:
                if kw in question_text:
                    return topic
        return "其他"

    def _generate_full_summary(self, questions: List[Dict]) -> Dict:
        """Generate a comprehensive knowledge summary."""
        topic_groups: Dict[str, List[Dict]] = defaultdict(list)
        for q in questions:
            topic = self._classify_topic(q["question"])
            topic_groups[topic].append(q)

        chapters = []
        for topic, qs in sorted(topic_groups.items(), key=lambda x: -len(x[1])):
            single = [q for q in qs if q["type"] == "single"]
            multi = [q for q in qs if q["type"] == "multiple"]
            tf = [q for q in qs if q["type"] == "truefalse"]

            # Key concepts from question text
            concepts = self._extract_concepts(qs)

            chapters.append({
                "topic": topic,
                "total_questions": len(qs),
                "single_choice": len(single),
                "multiple_choice": len(multi),
                "true_false": len(tf),
                "key_concepts": concepts,
                "difficulty": self._estimate_difficulty(qs),
                "sample_questions": [
                    {"id": q["id"], "text": q["question"][:80]}
                    for q in qs[:3]
                ],
            })

        return {
            "summary_type": "full_knowledge_summary",
            "total_questions": len(questions),
            "total_topics": len(chapters),
            "chapters": chapters,
            "overall_difficulty": self._estimate_difficulty(questions),
            "generated_at": datetime.now().isoformat(),
        }

    def _generate_chapter_summary(self, questions: List[Dict]) -> Dict:
        """Generate per-question detailed summary."""
        summaries = []
        for q in questions:
            topic = self._classify_topic(q["question"])
            key_points = self._extract_key_points(q)

            # Check correctness patterns
            correct_answers = list(q["answer"])
            wrong_options = [k for k in q["options"] if k not in correct_answers]

            explanations = {}
            for opt_key, opt_val in q["options"].items():
                explanations[opt_key] = {
                    "text": opt_val,
                    "is_correct": opt_key in correct_answers,
                    "explanation": self._option_explanation(q, opt_key),
                }

            summaries.append({
                "id": q["id"],
                "type": q["type"],
                "topic": topic,
                "question": q["question"],
                "correct_answer": q["answer"],
                "key_points": key_points,
                "option_analysis": explanations,
                "memory_tip": self._memory_tip(q),
            })

        return {
            "summary_type": "chapter_detail",
            "questions": summaries,
            "total": len(summaries),
        }

    def _generate_knowledge_cards(self, questions: List[Dict]) -> Dict:
        """Generate flashcard-style knowledge cards."""
        cards = []
        for q in questions:
            if q["type"] == "truefalse":
                cards.append({
                    "type": "card",
                    "front": q["question"],
                    "back": f"{'正确' if q['answer'] == 'A' else '错误'}",
                    "topic": self._classify_topic(q["question"]),
                })
            else:
                correct_text = " / ".join(
                    q["options"][k] for k in q["answer"]
                )
                cards.append({
                    "type": "card",
                    "front": q["question"],
                    "back": correct_text,
                    "topic": self._classify_topic(q["question"]),
                })

        return {
            "summary_type": "knowledge_cards",
            "cards": cards,
            "total": len(cards),
        }

    def _generate_knowledge_map(self, questions: List[Dict]) -> Dict:
        """Generate a hierarchical knowledge map."""
        topic_groups: Dict[str, List[str]] = defaultdict(set)
        for q in questions:
            topic = self._classify_topic(q["question"])
            for concept in self._extract_concepts([q]):
                topic_groups[topic].add(concept)

        nodes = []
        edges = []
        node_id = 0

        root_id = node_id
        nodes.append({"id": root_id, "label": "人工智能训练师", "level": 0})

        for topic, concepts in topic_groups.items():
            node_id += 1
            topic_id = node_id
            nodes.append({
                "id": topic_id, "label": topic,
                "parent": root_id, "level": 1,
                "question_count": sum(1 for q in questions
                    if self._classify_topic(q["question"]) == topic),
            })
            edges.append({"source": root_id, "target": topic_id, "type": "contains"})

            for concept in list(concepts)[:8]:
                node_id += 1
                nodes.append({
                    "id": node_id, "label": concept,
                    "parent": topic_id, "level": 2,
                })
                edges.append({"source": topic_id, "target": node_id, "type": "contains"})

        return {
            "summary_type": "knowledge_map",
            "nodes": nodes,
            "edges": edges,
            "total_topics": len(topic_groups),
            "total_concepts": sum(len(v) for v in topic_groups.values()),
        }

    def _analyze_by_topic(self, questions: List[Dict]) -> Dict:
        """Analyze question distribution by topic."""
        topic_stats = defaultdict(lambda: {"total": 0, "single": 0, "multiple": 0, "truefalse": 0})

        for q in questions:
            topic = self._classify_topic(q["question"])
            topic_stats[topic]["total"] += 1
            qtype = q.get("type", "")
            if qtype in topic_stats[topic]:
                topic_stats[topic][qtype] += 1

        ranked = sorted(
            topic_stats.items(), key=lambda x: -x[1]["total"]
        )

        return {
            "summary_type": "topic_analysis",
            "topics": [
                {
                    "name": name,
                    "stats": stats,
                    "percentage": round(
                        stats["total"] / len(questions) * 100, 1
                    ) if questions else 0,
                }
                for name, stats in ranked
            ],
        }

    def _extract_concepts(self, questions: List[Dict]) -> List[str]:
        """Extract key concepts from questions."""
        all_text = " ".join(q["question"] for q in questions)
        # Simple keyword extraction based on common AI terms
        ai_terms = [
            "机器学习", "深度学习", "神经网络", "训练", "测试", "模型",
            "数据", "采集", "标注", "特征", "算法", "分类", "回归",
            "聚类", "强化", "监督", "自然语言", "计算机视觉",
            "Python", "SQL", "数据库", "网络", "操作系统",
            "产品经理", "需求", "场景", "用户", "落地",
            "大数据", "分布式", "标注", "数据集",
        ]
        found = []
        for term in ai_terms:
            if term in all_text:
                found.append(term)
        return found[:10]

    def _extract_key_points(self, q: Dict) -> List[str]:
        """Extract key teaching points from a question."""
        points = []
        correct_opts = list(q["answer"])
        for opt_key in correct_opts:
            if opt_key in q["options"]:
                opt = q["options"][opt_key]
                if len(opt) > 5:
                    points.append(opt)

        # Add the question stem as a key point
        if len(points) < 2:
            text = q["question"]
            if "（" in text and "）" in text:
                parts = text.split("（")
                if len(parts) >= 2:
                    # Get context around the blank
                    points.append(parts[0][-30:].strip())

        return points[:4]

    def _estimate_difficulty(self, questions: List[Dict]) -> str:
        """Estimate overall difficulty."""
        if not questions:
            return "未知"
        multi_ratio = len([q for q in questions if q["type"] == "multiple"]) / len(questions)
        if multi_ratio > 0.3:
            return "困难"
        elif multi_ratio > 0.15:
            return "中等"
        return "基础"

    def _option_explanation(self, q: Dict, opt_key: str) -> str:
        """Generate brief explanation for each option."""
        is_correct = opt_key in q["answer"]
        if is_correct:
            return "✓ 这是正确答案"
        text = q["options"].get(opt_key, "")
        # Detect common wrong patterns
        if "一切" in text or "所有" in text:
            return "⚠ 表述过于绝对，通常是错误的"
        if "不" in text and q["type"] == "truefalse":
            return "⚠ 需要注意双重否定"
        return "✗ 这不是正确答案"

    def _memory_tip(self, q: Dict) -> str:
        """Generate a memory tip for the question."""
        tips = [
            "记住：正确选项往往是最准确、最严谨的表述",
            "含'一切'、'所有'的选项通常是错误的",
            "注意区分容易混淆的概念",
            "结合具体场景理解更容易记住",
            "这道题考查的是核心概念，需要重点掌握",
        ]
        return random.choice(tips)


class AnswerExplainerAgent(BaseAgent):
    """
    Provides detailed explanations for questions.
    Connects questions to knowledge points,
    explains why answers are right/wrong.
    """

    def __init__(self):
        super().__init__("ExplainerAgent", "题目解析专家")
        self.capabilities = ["答案解析", "知识点关联", "易错点提醒", "举一反三"]

        self.explanation_templates = {
            "single": self._explain_single,
            "multiple": self._explain_multiple,
            "truefalse": self._explain_truefalse,
        }

    async def _run(self, context: Dict) -> Dict:
        question = context.get("question", {})
        user_answers = context.get("user_answers", {})
        qtype = question.get("type", "single")

        explainer = self.explanation_templates.get(qtype, self._explain_single)
        result = explainer(question, user_answers)

        # Add knowledge connection
        result["knowledge_connections"] = self._connect_knowledge(question)

        # Add similar questions hint
        result["related_concepts"] = self._find_related_concepts(question)

        return result

    def _explain_single(self, q: Dict, user_answers: Dict) -> Dict:
        correct = q["answer"]
        user = user_answers.get(str(q["id"]), "")
        is_correct = user == correct

        explanation_parts = []

        if is_correct:
            explanation_parts.append("🎉 回答正确！")
        else:
            explanation_parts.append(f"❌ 回答错误。正确答案是：{q['options'].get(correct, correct)}")
            if user and user in q["options"]:
                explanation_parts.append(
                    f"你的选择 [{q['options'][user]}] 不正确，"
                    f"因为{q['options'][user][:20]}不符合题意。"
                )

        # Explain the correct answer
        if correct in q["options"]:
            explanation_parts.append(
                f"解析：正确答案 [{q['options'][correct]}] 是正确的，"
                f"因为它准确描述了{q['question'][:30]}相关知识。"
            )

        # Wrong answer analysis
        for opt_key in q["options"]:
            if opt_key != correct:
                explanation_parts.append(
                    f"选项 [{opt_key}] [{q['options'][opt_key]}] "
                    f"不符合要求，需要注意。"
                )

        return {
            "is_correct": is_correct,
            "correct_answer": correct,
            "correct_text": q["options"].get(correct, ""),
            "explanation": "\n".join(explanation_parts),
            "user_answer": user,
        }

    def _explain_multiple(self, q: Dict, user_answers: Dict) -> Dict:
        correct_set = set(q["answer"])
        user_set = set(user_answers.get(str(q["id"]), ""))

        is_correct = correct_set == user_set

        if is_correct:
            explanation = "🎉 全部选对！"
        else:
            missing = correct_set - user_set
            extra = user_set - correct_set
            parts = ["解析多选题答案："]
            parts.append(f"✓ 正确答案选项：{', '.join(sorted(correct_set))}")
            if missing:
                parts.append(f"⚠ 遗漏的选项：{', '.join(sorted(missing))}")
            if extra:
                parts.append(f"✗ 多余选择的选项：{', '.join(sorted(extra))}")
            explanation = "\n".join(parts)

        return {
            "is_correct": is_correct,
            "correct_answer": sorted(correct_set),
            "correct_texts": [q["options"][k] for k in sorted(correct_set) if k in q["options"]],
            "explanation": explanation,
            "user_answer": sorted(user_set),
        }

    def _explain_truefalse(self, q: Dict, user_answers: Dict) -> Dict:
        correct = q["answer"]
        user = user_answers.get(str(q["id"]), "")
        is_correct = user == correct
        verdict = "正确" if correct == "A" else "错误"

        explanation = f"这道题是{verdict}的。"
        explanation += f"正确答案：[{verdict}]。"

        if not is_correct:
            explanation += f"你的判断有误，请仔细分析题目中的知识点。"

        return {
            "is_correct": is_correct,
            "correct_answer": correct,
            "verdict": verdict,
            "explanation": explanation,
        }

    def _connect_knowledge(self, q: Dict) -> List[str]:
        """Connect question to broader knowledge areas."""
        text = q["question"]
        connections = []
        knowledge_map = {
            "数据采集": ["数据清洗", "数据标注", "数据集构建"],
            "机器学习": ["模型训练", "特征工程", "模型评估"],
            "深度学习": ["神经网络", "反向传播", "卷积网络"],
            "自然语言": ["词向量", "注意力机制", "Transformer"],
            "计算机视觉": ["图像分类", "目标检测", "图像分割"],
            "产品经理": ["用户需求", "场景分析", "产品落地"],
            "Python": ["数据类型", "函数", "控制流"],
            "数据库": ["SQL查询", "数据存储", "ETL"],
            "网络": ["TCP/IP", "HTTP", "网络安全"],
            "职业道德": ["工匠精神", "诚实守信", "爱岗敬业"],
        }
        for keyword, connected in knowledge_map.items():
            if keyword in text:
                connections.extend(connected)
        return connections[:5]

    def _find_related_concepts(self, q: Dict) -> List[str]:
        """Find concepts related to this question."""
        text = q["question"]
        concepts = []

        concept_keywords = {
            "数据采集": ["标注质量", "数据集", "采集场景"],
            "强化学习": ["奖励函数", "策略梯度", "Q值"],
            "监督学习": ["标注数据", "特征", "标签"],
            "神经网络": ["权重", "偏置", "激活函数"],
        }
        for concept, related in concept_keywords.items():
            if concept in text:
                concepts.extend(related)
        return concepts[:4]


class LearningAnalyzerAgent(BaseAgent):
    """
    Analyzes user learning progress.
    Identifies weak knowledge points,
    generates learning suggestions.
    """

    def __init__(self):
        super().__init__("AnalyzerAgent", "学习分析专家")
        self.capabilities = ["薄弱点识别", "学习建议", "进度跟踪", "知识掌握度"]

    async def _run(self, context: Dict) -> Dict:
        exam_records = context.get("exam_records", [])
        questions = context.get("questions", {})
        mode = context.get("mode", "full_analysis")

        if mode == "weak_points":
            return self._identify_weak_points(exam_records, questions)
        elif mode == "progress_report":
            return self._generate_progress_report(exam_records, questions)
        elif mode == "mastery_map":
            return self._generate_mastery_map(exam_records, questions)
        else:
            return self._full_analysis(exam_records, questions)

    def _full_analysis(self, records: List[Dict], questions: Dict) -> Dict:
        """Comprehensive learning analysis."""
        if not records:
            return self._empty_analysis()

        total = len(records)
        correct = sum(1 for r in records if r.get("is_correct", False))
        score_rate = correct / total * 100 if total else 0

        # By type analysis
        type_stats = defaultdict(lambda: {"total": 0, "correct": 0})
        for r in records:
            qid = r.get("question_id")
            q = questions.get(qid, {})
            qtype = q.get("type", "unknown")
            type_stats[qtype]["total"] += 1
            if r.get("is_correct"):
                type_stats[qtype]["correct"] += 1

        # By time analysis
        time_stats = self._analyze_time_distribution(records)

        # Accuracy trend
        trend = self._calculate_trend(records)

        return {
            "analysis_type": "full",
            "overview": {
                "total_answered": total,
                "correct": correct,
                "incorrect": total - correct,
                "score_rate": round(score_rate, 1),
                "grade": self._score_to_grade(score_rate),
            },
            "by_type": {
                k: {
                    "total": v["total"],
                    "correct": v["correct"],
                    "rate": round(
                        v["correct"] / v["total"] * 100, 1
                    ) if v["total"] else 0,
                }
                for k, v in type_stats.items()
            },
            "time_distribution": time_stats,
            "trend": trend,
            "suggestions": self._generate_suggestions(score_rate, type_stats),
        }

    def _identify_weak_points(self, records: List[Dict], questions: Dict) -> Dict:
        """Identify the user's weak knowledge points."""
        if not records:
            return {"weak_points": [], "strong_points": []}

        # Group by question
        wrong_qs = []
        correct_qs = []
        for r in records:
            if not r.get("is_correct"):
                wrong_qs.append(r.get("question_id"))
            else:
                correct_qs.append(r.get("question_id"))

        # Get question details for wrong answers
        weak_details = []
        strong_details = []

        wrong_counter = Counter(wrong_qs)
        correct_counter = Counter(correct_qs)

        for qid, wrong_count in wrong_counter.most_common():
            q = questions.get(qid, {})
            if q:
                weak_details.append({
                    "id": qid,
                    "question": q["question"][:80],
                    "type": q["type"],
                    "wrong_count": wrong_count,
                    "your_answer": "N/A",
                    "correct_answer": q["answer"],
                    "priority": "high" if wrong_count >= 3 else "medium",
                })

        for qid, correct_count in correct_counter.most_common(10):
            q = questions.get(qid, {})
            if q:
                strong_details.append({
                    "id": qid,
                    "question": q["question"][:80],
                    "correct_count": correct_count,
                })

        return {
            "weak_points": weak_details[:15],
            "strong_points": strong_details[:10],
            "total_weak": len(weak_details),
            "total_strong": len(strong_details),
        }

    def _generate_progress_report(self, records: List[Dict], questions: Dict) -> Dict:
        """Generate a detailed progress report."""
        if not records:
            return self._empty_analysis()

        # Group by date
        by_date = defaultdict(list)
        for r in records:
            date = r.get("timestamp", "unknown")[:10]
            by_date[date].append(r)

        daily_stats = []
        for date in sorted(by_date.keys()):
            day_records = by_date[date]
            correct = sum(1 for r in day_records if r.get("is_correct"))
            daily_stats.append({
                "date": date,
                "answered": len(day_records),
                "correct": correct,
                "rate": round(correct / len(day_records) * 100, 1) if day_records else 0,
            })

        # Streak calculation
        streak = self._calculate_streak(daily_stats)

        return {
            "report_type": "progress",
            "daily_stats": daily_stats,
            "streak_days": streak,
            "total_days": len(daily_stats),
            "recommendation": self._progress_recommendation(daily_stats),
        }

    def _generate_mastery_map(self, records: List[Dict], questions: Dict) -> Dict:
        """Generate knowledge mastery map."""
        mastery: Dict[str, List[int]] = defaultdict(list)
        for r in records:
            qid = r.get("question_id")
            q = questions.get(qid, {})
            topic = q.get("topic", "未分类")
            mastery[topic].append(1 if r.get("is_correct") else 0)

        mastery_map = {}
        for topic, results in mastery.items():
            total = len(results)
            correct = sum(results)
            mastery_map[topic] = {
                "total": total,
                "correct": correct,
                "mastery": round(correct / total * 100, 1) if total else 0,
                "level": self._mastery_level(correct / total * 100 if total else 0),
            }

        return {
            "mastery_map": mastery_map,
            "total_topics": len(mastery_map),
        }

    def _analyze_time_distribution(self, records: List[Dict]) -> Dict:
        """Analyze when the user studies best."""
        hours = []
        for r in records:
            ts = r.get("timestamp", "")
            if ts:
                try:
                    hour = int(ts[11:13]) if len(ts) > 11 else 12
                    hours.append(hour)
                except (ValueError, IndexError):
                    pass

        if not hours:
            return {"peak_hours": [], "distribution": {}}

        hour_counts = Counter(hours)
        peak = [h for h, c in hour_counts.most_common(3)]

        return {
            "peak_hours": peak,
            "total_records": len(hours),
            "distribution": dict(sorted(hour_counts.items())),
        }

    def _calculate_trend(self, records: List[Dict]) -> Dict:
        """Calculate accuracy trend."""
        if len(records) < 5:
            return {"direction": "unknown", "recent_rate": 0}

        recent = records[-10:]
        recent_rate = (
            sum(1 for r in recent if r.get("is_correct")) / len(recent) * 100
        )
        older = records[:10]
        older_rate = (
            sum(1 for r in older if r.get("is_correct")) / len(older) * 100
        )

        direction = "improving" if recent_rate > older_rate else (
            "declining" if recent_rate < older_rate else "stable"
        )

        return {
            "direction": direction,
            "recent_rate": round(recent_rate, 1),
            "overall_rate": round(older_rate, 1),
            "change": round(recent_rate - older_rate, 1),
        }

    def _calculate_streak(self, daily_stats: List[Dict]) -> int:
        """Calculate study streak days."""
        streak = 0
        for day in reversed(daily_stats):
            if day["answered"] > 0:
                streak += 1
            else:
                break
        return streak

    def _score_to_grade(self, rate: float) -> str:
        if rate >= 90:
            return "优秀"
        elif rate >= 75:
            return "良好"
        elif rate >= 60:
            return "及格"
        return "需加强"

    def _mastery_level(self, rate: float) -> str:
        if rate >= 90:
            return "精通"
        elif rate >= 75:
            return "熟练"
        elif rate >= 60:
            return "理解"
        elif rate >= 30:
            return "了解"
        return "薄弱"

    def _generate_suggestions(self, score_rate: float, type_stats: Dict) -> List[str]:
        """Generate personalized learning suggestions."""
        suggestions = []

        if score_rate >= 90:
            suggestions.append("🏆 表现优秀！建议开始模拟考试冲刺")
            suggestions.append("📚 可以重点关注多选题和难题")
        elif score_rate >= 75:
            suggestions.append("👍 基础扎实，继续巩固易错知识点")
            suggestions.append("🎯 建议重点练习薄弱题型")
        elif score_rate >= 60:
            suggestions.append("💪 基础尚可，需要加强练习")
            suggestions.append("📖 建议重新学习薄弱章节")
        else:
            suggestions.append("🔧 需要系统性地重新学习")
            suggestions.append("📝 建议从单选题开始逐步建立信心")

        for qtype, stats in type_stats.items():
            rate = stats["correct"] / stats["total"] * 100 if stats["total"] else 0
            if rate < 50:
                type_name = {
                    "single": "单选题",
                    "multiple": "多选题",
                    "truefalse": "判断题",
                }.get(qtype, qtype)
                suggestions.append(f"⚠ {type_name}正确率较低({rate:.0f}%)，需要专项训练")

        return suggestions

    def _progress_recommendation(self, daily_stats: List[Dict]) -> str:
        """Generate progress recommendation."""
        if not daily_stats:
            return "开始你的第一次答题吧！"

        avg = sum(d["answered"] for d in daily_stats) / len(daily_stats)
        if avg >= 30:
            return "学习强度大，注意劳逸结合，建议复习效率"
        elif avg >= 15:
            return "学习节奏良好，继续保持！"
        else:
            return "建议适当增加每日练习量以达到考试要求"

    def _empty_analysis(self) -> Dict:
        return {
            "overview": {
                "total_answered": 0,
                "correct": 0,
                "score_rate": 0,
                "grade": "未开始",
            },
            "suggestions": ["开始答题获取个性化分析"],
        }


class ExamPredictorAgent(BaseAgent):
    """
    Predicts high-frequency exam points.
    Analyzes question patterns and distributions.
    """

    def __init__(self):
        super().__init__("PredictorAgent", "考点预测专家")
        self.capabilities = ["高频考点", "出题规律", "复习重点", "押题分析"]

    async def _run(self, context: Dict) -> Dict:
        questions = context.get("questions", [])
        mode = context.get("mode", "full_prediction")

        if mode == "high_frequency":
            return self._predict_high_frequency(questions)
        elif mode == "key_points":
            return self._extract_key_points_for_exam(questions)
        elif mode == "review_plan":
            return self._generate_review_plan(questions)
        else:
            return self._full_prediction(questions)

    def _full_prediction(self, questions: List[Dict]) -> Dict:
        """Comprehensive exam prediction analysis."""
        high_freq = self._predict_high_frequency(questions)
        key_points = self._extract_key_points_for_exam(questions)

        return {
            "prediction_type": "full",
            "high_frequency": high_freq,
            "key_points": key_points,
            "exam_strategy": self._generate_exam_strategy(),
        }

    def _predict_high_frequency(self, questions: List[Dict]) -> Dict:
        """Identify high-frequency exam points."""
        # Group by topic and rank
        topic_stats = defaultdict(lambda: {"count": 0, "examples": []})
        for q in questions:
            text = q["question"]
            topic = "其他"
            for kw, topics in [
                ("Python", "Python编程"),
                ("数据", "数据采集与处理"),
                ("机器学习", "机器学习"),
                ("深度学习", "深度学习"),
                ("算法", "算法基础"),
                ("网络", "网络技术"),
                ("操作系统", "操作系统"),
                ("产品", "AI产品设计"),
                ("数据库", "数据库"),
                ("道德", "职业道德"),
                ("采集", "数据采集"),
                ("模型", "模型训练"),
                ("自然语言", "自然语言处理"),
                ("视觉", "计算机视觉"),
                ("强化", "强化学习"),
            ]:
                if kw in text:
                    topic = topics
                    break
            topic_stats[topic]["count"] += 1
            if len(topic_stats[topic]["examples"]) < 2:
                topic_stats[topic]["examples"].append(q["question"][:60])

        ranked = sorted(topic_stats.items(), key=lambda x: -x[1]["count"])

        return {
            "prediction_type": "high_frequency",
            "topics": [
                {
                    "rank": i + 1,
                    "topic": name,
                    "question_count": stats["count"],
                    "percentage": round(
                        stats["count"] / len(questions) * 100, 1
                    ),
                    "importance": self._importance_level(
                        stats["count"] / len(questions)
                    ),
                    "examples": stats["examples"],
                }
                for i, (name, stats) in enumerate(ranked[:10])
            ],
        }

    def _extract_key_points_for_exam(self, questions: List[Dict]) -> Dict:
        """Extract key exam points."""
        # Focus on multiple choice questions (usually more complex)
        important_qs = [q for q in questions if q["type"] == "multiple"]
        important_qs.extend(q for q in questions if q["type"] == "single" and len(q["options"]) == 4)

        # Get questions from high-value topics
        valuable_topics = ["机器学习", "深度学习", "Python编程", "数据采集", "AI产品设计"]
        key_qs = []
        for q in questions:
            for kw in valuable_topics:
                if kw in q["question"]:
                    key_qs.append(q)
                    break

        return {
            "prediction_type": "key_points",
            "total_key": len(key_qs),
            "questions": [
                {"id": q["id"], "text": q["question"][:80], "type": q["type"]}
                for q in key_qs[:30]
            ],
        }

    def _generate_review_plan(self, questions: List[Dict]) -> Dict:
        """Generate a review plan."""
        topics = self._predict_high_frequency(questions)["topics"]

        plan_items = []
        for i, topic in enumerate(topics[:8]):
            difficulty = "困难" if i < 3 else ("中等" if i < 6 else "基础")
            plan_items.append({
                "order": i + 1,
                "topic": topic["topic"],
                "priority": topic["importance"],
                "estimated_time": 15 + i * 5,
                "difficulty": difficulty,
                "action": self._review_action(difficulty),
            })

        return {
            "plan_type": "review",
            "total_items": len(plan_items),
            "estimated_hours": sum(p["estimated_time"] for p in plan_items) / 60,
            "plan": plan_items,
        }

    def _generate_exam_strategy(self) -> Dict:
        """Generate exam strategy recommendations."""
        return {
            "time_management": {
                "total_minutes": 90,
                "single_per_question": 0.8,
                "multiple_per_question": 1.5,
                "truefalse_per_question": 0.5,
            },
            "answering_strategy": [
                "先做简单题（判断题→单选题→多选题）",
                "多选题不确定时少选比错选得分更有保障",
                "留5-10分钟检查",
                "含'一切'、'所有'的选项通常错误",
                "最准确严谨的表述通常是正确答案",
            ],
            "difficulty_priority": "先易后难，确保基础分",
        }

    def _importance_level(self, ratio: float) -> str:
        if ratio >= 0.15:
            return "核心考点"
        elif ratio >= 0.08:
            return "重要考点"
        elif ratio >= 0.04:
            return "一般考点"
        return "了解即可"

    def _review_action(self, difficulty: str) -> str:
        actions = {
            "困难": "精讲+大量练习+举一反三",
            "中等": "理解+常规练习+错题回顾",
            "基础": "快速过+选择题库+确保掌握",
        }
        return actions.get(difficulty, "常规学习")


class StudyPlannerAgent(BaseAgent):
    """
    Creates personalized study plans.
    Manages time allocation and progress tracking.
    """

    def __init__(self):
        super().__init__("PlannerAgent", "学习规划专家")
        self.capabilities = ["学习计划", "时间管理", "进度跟踪", "个性化推荐"]

    async def _run(self, context: Dict) -> Dict:
        plan_type = context.get("plan_type", "exam_prep")
        exam_date = context.get("exam_date", "")
        daily_minutes = context.get("daily_minutes", 30)
        current_level = context.get("current_level", "beginner")

        if plan_type == "exam_prep":
            return self._create_exam_plan(exam_date, daily_minutes, current_level)
        elif plan_type == "streak_recovery":
            return self._create_recovery_plan(daily_minutes)
        else:
            return self._create_custom_plan(daily_minutes)

    def _create_exam_plan(
        self, exam_date: str, daily_minutes: int, level: str
    ) -> Dict:
        """Create an exam preparation plan."""
        from datetime import datetime, timedelta

        try:
            target = datetime.fromisoformat(exam_date)
            days_left = (target - datetime.now()).days
        except (ValueError, TypeError):
            days_left = 14

        if days_left <= 0:
            days_left = 1
        if daily_minutes <= 0:
            daily_minutes = 30

        total_minutes = days_left * daily_minutes

        # Phase allocation
        if days_left >= 14:
            phases = [
                {"name": "第1-7天", "phase": "基础学习", "focus": "系统学习各章节", "questions": 200},
                {"name": "第8-14天", "phase": "强化练习", "focus": "专项练习+错题回顾", "questions": 200},
                {"name": "最后3天", "phase": "模拟冲刺", "focus": "全真模拟+查漏补缺", "questions": 100},
            ]
        elif days_left >= 7:
            phases = [
                {"name": "第1-3天", "phase": "重点突破", "focus": "高频考点+核心概念", "questions": 150},
                {"name": "第4-5天", "phase": "专项训练", "focus": "薄弱题型+易错点", "questions": 150},
                {"name": "最后2天", "phase": "模拟冲刺", "focus": "全真模拟+知识回顾", "questions": 100},
            ]
        else:
            phases = [
                {"name": "第1天", "phase": "高频复习", "focus": "核心考点+高频题", "questions": 200},
                {"name": "第2天", "phase": "错题+难题", "focus": "易错题+多选题", "questions": 150},
                {"name": "考试前一天", "phase": "知识回顾", "focus": "知识卡片+快速过", "questions": 50},
            ]

        daily_plans = []
        remaining = 500
        for day in range(min(days_left, 14)):
            phase = phases[0] if day < days_left // 3 else (
                phases[1] if day < days_left * 2 // 3 else phases[2]
            )
            q_count = min(30 + (10 if level == "advanced" else 5), remaining)
            remaining -= q_count
            daily_plans.append({
                "day": day + 1,
                "phase": phase["phase"],
                "focus": phase["focus"],
                "target_questions": q_count,
                "estimated_minutes": daily_minutes,
                "study_tips": self._daily_tip(day),
            })

        return {
            "plan_type": "exam_prep",
            "days_left": days_left,
            "daily_minutes": daily_minutes,
            "total_questions": 500,
            "total_hours": round(total_minutes / 60, 1),
            "phases": phases,
            "daily_plans": daily_plans[:min(days_left, 14)],
            "milestones": self._milestones(days_left),
        }

    def _create_recovery_plan(self, daily_minutes: int) -> Dict:
        """Create a plan to recover from a learning gap."""
        return {
            "plan_type": "recovery",
            "strategy": "分层恢复",
            "daily_plans": [
                {"day": 1, "focus": "单选题基础", "questions": 30, "tip": "建立信心"},
                {"day": 2, "focus": "单选题强化", "questions": 40, "tip": "巩固基础"},
                {"day": 3, "focus": "判断题训练", "questions": 30, "tip": "快速题型"},
                {"day": 4, "focus": "多选题专项", "questions": 20, "tip": "难点突破"},
                {"day": 5, "focus": "综合模拟", "questions": 50, "tip": "检验效果"},
            ],
        }

    def _create_custom_plan(self, daily_minutes: int) -> Dict:
        """Create a custom flexible plan."""
        q_count = daily_minutes // 1.5
        return {
            "plan_type": "custom",
            "daily_minutes": daily_minutes,
            "daily_questions": int(q_count),
            "recommendation": f"每天完成{int(q_count)}道题，7天可以学完500题",
        }

    def _daily_tip(self, day: int) -> str:
        tips = [
            "今天保持专注，建立学习节奏",
            "注意休息，每25分钟休息5分钟",
            "整理第一天的错题",
            "尝试挑战一些稍难的题目",
            "复习前三天的薄弱知识点",
            "练习题要计时，模拟考试节奏",
            "整理本周的错题本",
            "尝试不看答案独立思考",
            "多选题注意'少选不扣分'的规则",
            "复习核心概念的定义",
            "做一套模拟题检验学习成果",
            "总结易混淆知识点",
            "过一遍知识卡片",
            "保持良好作息，调整状态",
        ]
        return tips[min(day, len(tips) - 1)]

    def _milestones(self, days_left: int) -> List[Dict]:
        """Define study milestones."""
        return [
            {"day": max(1, days_left // 3), "milestone": "完成基础学习", "checkpoint": "单选题80%掌握"},
            {"day": max(2, days_left * 2 // 3), "milestone": "完成专项训练", "checkpoint": "正确率75%"},
            {"day": max(3, days_left - 2), "milestone": "进入冲刺阶段", "checkpoint": "全真模拟合格"},
        ]


class AgentOrchestrator:
    """
    Coordinates multiple AI agents.
    Manages inter-agent communication and task distribution.
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "summarizer": KnowledgeSummarizerAgent(),
            "explainer": AnswerExplainerAgent(),
            "analyzer": LearningAnalyzerAgent(),
            "predictor": ExamPredictorAgent(),
            "planner": StudyPlannerAgent(),
        }
        self.message_queue: List[Message] = []
        self.execution_log: List[Dict] = []

    def get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        return self.agents.get(agent_type)

    def list_agents(self) -> List[Dict]:
        """List all available agents."""
        return [
            {
                "id": agent_id,
                "name": agent.name,
                "role": agent.role,
                "capabilities": agent.capabilities,
            }
            for agent_id, agent in self.agents.items()
        ]

    async def execute_single(self, agent_type: str, context: Dict) -> AgentResult:
        """Execute a single agent by type."""
        agent = self.agents.get(agent_type)
        if not agent:
            return AgentResult(
                agent=agent_type, success=False,
                data={"error": f"Unknown agent: {agent_type}"},
            )
        return await agent.execute(context)

    async def execute_pipeline(
        self, pipeline: List[tuple], context: Dict
    ) -> Dict[str, AgentResult]:
        """Execute a sequence of agents (pipeline)."""
        results = {}
        current_context = context.copy()

        for agent_type, input_key in pipeline:
            result = await self.execute_single(agent_type, current_context)
            results[agent_type] = result
            self.execution_log.append({
                "agent": agent_type,
                "success": result.success,
                "time_ms": result.execution_time_ms,
            })

            # Chain results
            if result.success:
                current_context[input_key] = result.data

        return results

    async def execute_full_analysis(self, context: Dict) -> Dict:
        """
        Execute a complete AI analysis pipeline:
        Summarizer -> Analyzer -> Predictor -> Planner
        """
        pipeline = [
            ("summarizer", "summary"),
            ("analyzer", "analysis"),
            ("predictor", "prediction"),
            ("planner", "plan"),
        ]
        results = await self.execute_pipeline(pipeline, context)

        return {
            "pipeline": "full_analysis",
            "results": {
                k: {
                    "success": v.success,
                    "data": v.data,
                    "time_ms": v.execution_time_ms,
                }
                for k, v in results.items()
            },
            "total_time_ms": sum(
                v.execution_time_ms for v in results.values()
            ),
            "agents_used": list(results.keys()),
        }

    async def execute_exam_help(self, question: Dict, user_answer: str) -> Dict:
        """
        Execute exam help: Explainer -> Analyzer (for weak points)
        """
        context = {"question": question, "user_answers": {"answer": user_answer}}
        pipeline = [
            ("explainer", "explanation"),
            ("summarizer", "knowledge_summary"),
        ]
        results = await self.execute_pipeline(pipeline, context)

        return {
            "type": "exam_help",
            "explanation": results.get("explainer", AgentResult("", False, {})).data,
            "knowledge_context": results.get("summarizer", AgentResult("", False, {})).data,
        }

    async def generate_study_materials(
        self, questions: List[Dict]
    ) -> Dict:
        """
        Generate comprehensive study materials using all agents.
        """
        # Execute agents in parallel
        summarizer_ctx = {"questions": questions, "mode": "full_summary"}
        predictor_ctx = {"questions": questions, "mode": "full_prediction"}
        planner_ctx = {"plan_type": "exam_prep"}

        results = await asyncio.gather(
            self.agents["summarizer"].execute(summarizer_ctx),
            self.agents["predictor"].execute(predictor_ctx),
            self.agents["planner"].execute(planner_ctx),
        )

        return {
            "type": "study_materials",
            "knowledge_summary": results[0].data if results[0].success else {},
            "exam_prediction": results[1].data if results[1].success else {},
            "study_plan": results[2].data if results[2].success else {},
            "total_generation_time_ms": sum(r.execution_time_ms for r in results),
        }


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
