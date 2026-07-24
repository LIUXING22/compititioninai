"""AI-backed wrong-answer explanations with a deterministic local fallback.
Supports OpenAI-compatible Chat Completions API (StepFun, OpenAI, etc.)
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Tuple

import httpx
from dotenv import load_dotenv


load_dotenv(override=True)

DEFAULT_MODEL = "gpt-5-mini"


class AIExplanationService:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        self.base_url = os.getenv("OPENAI_BASE_URL", "").strip().rstrip("/")
        self.timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    async def explain(self, question: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
        started = time.perf_counter()
        fallback_reason = ""

        if self.configured:
            try:
                data = await self._request_api(question, user_answer)
                data["source"] = "cloud"
                return {
                    "success": True,
                    "data": data,
                    "model": self.model,
                    "execution_time_ms": round((time.perf_counter() - started) * 1000, 1),
                }
            except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as exc:
                fallback_reason = self._safe_error(exc)
        else:
            fallback_reason = "未配置AI服务，已使用本地解析"

        data = self._local_explanation(question, user_answer)
        data["source"] = "local"
        data["fallback_reason"] = fallback_reason
        return {
            "success": True,
            "data": data,
            "model": None,
            "execution_time_ms": round((time.perf_counter() - started) * 1000, 1),
        }

    async def _request_api(
        self, question: Dict[str, Any], user_answer: str
    ) -> Dict[str, Any]:
        context = self._question_context(question, user_answer)
        system_prompt = (
            "你是考试辅导老师。输出JSON，不要输出思考过程、Markdown或其他文字。"
            "JSON字段：summary(简评)、reasoning(详细依据)、mistake_analysis(错误分析)、"
            "knowledge_points([知识点])、study_tip(记忆建议)。"
        )
        user_prompt = (
            f"用户选了{context['user_answer_text']}，正确答案是{context['correct_answer_text']}。"
            f"题目：{context['question']}"
        )

        # Build URL - use chat/completions endpoint
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 900,
            "temperature": 0.3,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()

        output_text = self._extract_chat_output(response_data)
        parsed = self._parse_json_output(output_text)
        return self._normalize_ai_data(parsed, question)

    def _question_context(
        self, question: Dict[str, Any], user_answer: str
    ) -> Dict[str, Any]:
        options = question.get("options") or {}
        correct_answer = self._normalize_answer(question.get("answer", ""))
        normalized_user = self._normalize_answer(user_answer)
        return {
            "question_id": question.get("id"),
            "question_type": question.get("type"),
            "question": str(question.get("question", ""))[:3000],
            "options": {str(k): str(v)[:1000] for k, v in options.items()},
            "correct_answer": correct_answer,
            "correct_answer_text": self._answer_text(options, correct_answer),
            "user_answer": normalized_user or "未作答",
            "user_answer_text": self._answer_text(options, normalized_user),
        }

    @staticmethod
    def _extract_chat_output(response_data: Dict[str, Any]) -> str:
        """Extract text from Chat Completions API response."""
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError("API响应中没有choices")

        message = choices[0].get("message", {})

        # Try content first, then reasoning_content, then reasoning
        content = message.get("content", "") or ""
        if content.strip():
            return content.strip()

        reasoning_content = message.get("reasoning_content", "") or ""
        if reasoning_content.strip():
            return reasoning_content.strip()

        reasoning = message.get("reasoning", "") or ""
        if reasoning.strip():
            return reasoning.strip()

        raise ValueError("API响应中content为空")

    @staticmethod
    def _parse_json_output(text: str, question: Dict[str, Any] = None) -> Dict[str, Any]:
        """Parse JSON from AI response, handling code blocks and mixed content.
        Falls back to plain text wrapping if JSON parsing fails."""
        cleaned = text.strip()

        # Remove code block markers if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)

        # If it's already valid JSON, return it
        if cleaned.startswith("{") and cleaned.endswith("}"):
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

        # Try to extract JSON object from mixed content (e.g., thinking + JSON)
        # Use brace counting to find the complete JSON object
        start = cleaned.find("{")
        if start >= 0:
            depth = 0
            in_string = False
            escape_next = False
            for i in range(start, len(cleaned)):
                ch = cleaned[i]
                if escape_next:
                    escape_next = False
                    continue
                if ch == '\\\\':
                    escape_next = True
                    continue
                if ch == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        # Found the complete JSON object
                        json_str = cleaned[start:i + 1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            break

        # If all else fails, treat as plain text and wrap in expected format
        correct = AIExplanationService._normalize_answer(question.get("answer", "")) if question else ""
        return {
            "summary": cleaned[:200] if cleaned else "AI返回内容无法解析",
            "reasoning": cleaned,
            "mistake_analysis": "AI以文本形式返回，未按JSON格式输出",
            "knowledge_points": AIExplanationService._infer_knowledge_points(
                str(question.get("question", "")) if question else ""
            ),
            "study_tip": "建议重新查看题目解析",
            "correct_answer": correct,
        }

    def _normalize_ai_data(
        self, data: Dict[str, Any], question: Dict[str, Any]
    ) -> Dict[str, Any]:
        required_text = ("summary", "reasoning", "mistake_analysis", "study_tip")
        result = {key: str(data.get(key, "")).strip() for key in required_text}
        if not all(result.values()):
            raise ValueError("AI返回的解析字段不完整")
        points = data.get("knowledge_points", [])
        if not isinstance(points, list):
            points = [str(points)]
        result["knowledge_points"] = [str(item).strip() for item in points if str(item).strip()][:6]
        result["correct_answer"] = self._normalize_answer(question.get("answer", ""))
        return result

    def _local_explanation(
        self, question: Dict[str, Any], user_answer: str
    ) -> Dict[str, Any]:
        options = question.get("options") or {}
        correct = self._normalize_answer(question.get("answer", ""))
        user = self._normalize_answer(user_answer)
        correct_text = self._answer_text(options, correct)
        user_text = self._answer_text(options, user) if user else "未作答"
        qtype = question.get("type", "single")

        if qtype == "multiple":
            missing = sorted(set(correct) - set(user))
            extra = sorted(set(user) - set(correct))
            details = []
            if missing:
                details.append(f"漏选了 {', '.join(missing)}")
            if extra:
                details.append(f"多选了 {', '.join(extra)}")
            mistake = "；".join(details) or "选项组合与标准答案不一致"
            tip = "多选题先逐项判断，再核对是否存在漏选或把相近概念误当成正确项。"
        elif qtype == "truefalse":
            mistake = "对题干中的适用范围或绝对化表述判断有误"
            tip = '判断题重点检查“一定、全部、仅”等限定词，并回到概念的适用条件。'
        else:
            mistake = "选择的选项与题目考查的核心定义不匹配"
            tip = "先提取题干关键词，再比较各选项与定义的必要条件。"

        points = self._infer_knowledge_points(str(question.get("question", "")))
        return {
            "summary": f"正确答案是 {correct or '题库未提供'}，你的答案是 {user or '未作答'}。",
            "reasoning": f"标准答案对应：{correct_text or '暂无选项文本'}。你的选择对应：{user_text}。",
            "mistake_analysis": mistake,
            "knowledge_points": points,
            "study_tip": tip,
            "correct_answer": correct,
        }

    @staticmethod
    def _infer_knowledge_points(question_text: str) -> List[str]:
        topics: List[Tuple[Tuple[str, ...], str]] = [
            (("机器学习", "监督学习", "分类", "回归"), "机器学习基础"),
            (("深度学习", "神经网络", "卷积", "反向传播"), "深度学习"),
            (("数据", "采集", "清洗", "标注"), "数据处理"),
            (("Python", "函数", "列表", "字典"), "Python 编程"),
            (("自然语言", "NLP", "文本"), "自然语言处理"),
            (("视觉", "图像", "目标检测"), "计算机视觉"),
            (("伦理", "隐私", "安全", "道德"), "人工智能伦理与安全"),
        ]
        matched = [label for keywords, label in topics if any(k in question_text for k in keywords)]
        return matched[:4] or ["题目核心概念与适用条件"]

    @staticmethod
    def _normalize_answer(answer: Any) -> str:
        if isinstance(answer, list):
            answer = "".join(str(item) for item in answer)
        return "".join(sorted({c for c in str(answer).upper() if c.isalpha()}))

    @staticmethod
    def _answer_text(options: Dict[str, Any], answer: str) -> str:
        return "；".join(
            f"{key}. {options[key]}" for key in answer if key in options
        )

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code if exc.response else "?"
            return f"AI服务请求失败（HTTP {status}），已使用本地解析"
        if isinstance(exc, httpx.TimeoutException):
            return "AI服务请求超时，已使用本地解析"
        return f"AI服务返回内容不可用（{type(exc).__name__}），已使用本地解析"


def get_ai_explanation_status() -> Dict[str, Any]:
    service = AIExplanationService()
    return {
        "configured": service.configured,
        "model": service.model if service.configured else None,
        "base_url": service.base_url if service.configured else None,
        "fallback_available": True,
    }


async def explain_wrong_answer(
    question: Dict[str, Any], user_answer: str
) -> Dict[str, Any]:
    return await AIExplanationService().explain(question, user_answer)
