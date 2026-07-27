"""
Advanced RAG service with 5 optimization layers:
1. Hybrid Search (TF-IDF + BM25 + RRF fusion) - in embedding_service
2. Rerank (LLM-based fine-grained relevance scoring)
3. Query Rewrite (formalize + decompose ambiguous queries)
4. Parent-Document RAG (small chunks for retrieval, large blocks for generation)
5. Self-RAG (adaptive decision: retrieve or not?)
"""
import json
import os
import re
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

from app.services.document_parser import DocumentChunk
from app.services.embedding_service import get_vector_store

load_dotenv(override=True)

# ── Config ─────────────────────────────────────────────────────────────

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "step-3.7-flash").strip() or "step-3.7-flash"
BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip().rstrip("/")
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))

SYSTEM_PROMPT = """你是人工智能训练师考试的智能助教。你的核心任务是帮助考生高效备考。

## 能力范围
- 人工智能基础知识（机器学习、深度学习、强化学习、计算机视觉、NLP等）
- 计算机基础（硬件、操作系统、网络、数据库等）
- Python编程基础
- 数据采集与处理
- AI产品设计与落地
- 职业道德与规范

## 回答规则
1. **优先基于提供的参考文档回答**：当检索到相关文档片段时，严格基于文档内容回答
2. **引用来源**：如果使用了文档内容，要指出来自哪个文档
3. **无匹配时如实说明**：如果文档中没有相关信息，基于你的知识补充，但明确说明"文档中未找到相关内容，以下为通用知识解答"
4. **简洁准确**：回答要简洁、准确，适合备考使用
5. **友好引导**：如果问题完全超出考试范围，友好引导用户回到备考相关话题

## 检索到的参考文档片段
{doc_context}

## 相关题目
{question_context}

请基于以上内容回答用户的问题。"""

# ── Quick LLM call helper ──────────────────────────────────────────────

async def _quick_llm(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 100,
    temperature: float = 0.0,
) -> str:
    """Fast, minimal LLM call for lightweight decisions."""
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=min(TIMEOUT, 10)) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return ""


# ── 5. Self-RAG: should we retrieve? ───────────────────────────────────

GREETING_PATTERNS = [
    "你好", "谢谢", "再见", "你是谁", "你叫什么", "hello", "hi",
    "退出", "拜拜", "感谢", "多谢", "好滴", "ok", "OK",
]

OUT_OF_SCOPE_PATTERNS = [
    "天气", "股票", "新闻", "电影", "音乐", "游戏", "吃饭",
    "几点", "今天", "明天", "NBA", "足球", "NBA", "外卖",
]

FOLLOW_UP_PATTERNS = [
    "再解释", "详细说", "为什么", "什么意思", "更多", "举个例子",
    "具体", "深入", "进一步",
]


def _is_greeting(message: str) -> bool:
    msg = message.lower().strip()
    return any(p.lower() in msg for p in GREETING_PATTERNS)


def _is_out_of_scope(message: str) -> bool:
    msg = message.lower().strip()
    return any(p.lower() in msg for p in OUT_OF_SCOPE_PATTERNS)


def _is_follow_up(message: str, history: Optional[List[Dict]] = None) -> bool:
    """Check if user is asking a follow-up to previous answer."""
    if not history or len(history) < 2:
        return False
    msg = message.lower().strip()
    if len(msg) < 20 and any(p in msg for p in FOLLOW_UP_PATTERNS):
        return True
    return False


async def should_retrieve(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> bool:
    """Self-RAG: decide whether to search document index."""
    # Rule-based fast path (zero overhead)
    if _is_greeting(message):
        return False
    if _is_out_of_scope(message):
        return False
    if _is_follow_up(message, history):
        # Reuse previous context, don't re-retrieve
        return False

    # If question is short and vague, let LLM decide
    if len(message.strip()) < 8:
        prompt = f"以下用户问题是否需要从考试题库中检索资料来回答？只需回复 yes 或 no。\n问题：{message}"
        result = await _quick_llm(
            "你是判断是否需要检索文档的决策器。",
            prompt,
            max_tokens=5,
        )
        return "yes" in result.lower()

    # Default: retrieve for substantive questions
    return True


# ── 3. Query Rewrite ───────────────────────────────────────────────────

async def rewrite_query(message: str) -> Tuple[str, List[str]]:
    """Rewrite ambiguous/spoken query into formal search-friendly form.
    Returns: (rewritten_main_query, [sub_queries])
    """
    msg = message.strip()

    # Quick heuristic: if already formal, skip rewriting
    if len(msg) >= 15 and not _looks_ambiguous(msg):
        return msg, []

    prompt = f"""将以下口语化问题改写为正式、完整的考试相关检索查询。
如果原始问题已经清晰，直接返回原始问题。
如果问题包含多个子问题，拆解为独立的检索查询。
返回JSON格式：{{"rewritten": "改写后主查询", "sub_queries": ["子查询1", "子查询2"]}}

原始问题：{msg}"""

    result = await _quick_llm(
        "你是查询改写器。将口语化问题改写为正式检索查询。",
        prompt,
        max_tokens=200,
    )

    if not result:
        return msg, []

    try:
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)

        # Extract JSON from possible mixed output
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(cleaned[start:end + 1])
            rewritten = data.get("rewritten", msg)
            sub_queries = data.get("sub_queries", [])
            if isinstance(sub_queries, list):
                return rewritten.strip(), [q.strip() for q in sub_queries if q.strip()]
            return rewritten.strip(), []
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback: return cleaned result as rewritten
    first_line = result.split("\n")[0].strip()
    if first_line and len(first_line) > 3:
        return first_line, []
    return msg, []


def _looks_ambiguous(message: str) -> bool:
    """Heuristic: does the query look spoken/ambiguous?"""
    msg = message.strip()
    # Very short
    if len(msg) < 6:
        return True
    # Contains spoken filler
    fillers = ["内个", "那个", "啥", "咋", "咋整", "呗", "嘛", "讷"]
    if any(f in msg for f in fillers):
        return True
    # No question keyword
    question_words = ["什么", "哪个", "怎么", "如何", "为什么", "定义", "解释", "区别"]
    if not any(q in msg for q in question_words) and len(msg) < 10:
        return True
    return False


# ── 2. Rerank ──────────────────────────────────────────────────────────

async def rerank_chunks(
    query: str,
    candidates: List[Tuple[DocumentChunk, float]],
    top_k: int = 5,
) -> List[Tuple[DocumentChunk, float]]:
    """LLM-based fine-grained reranking of coarse retrieval results."""
    if len(candidates) <= top_k:
        return candidates

    # Build candidate list for LLM
    items = []
    for idx, (chunk, score) in enumerate(candidates[:20]):
        excerpt = chunk.text[:200].replace("\n", " ")
        items.append(f"[{idx}] (retrieval_score={score:.3f}) {excerpt}")

    prompt = f"""你是文档相关性评分器。根据用户查询，对候选文档片段按相关性排序。
只返回JSON：{{"ranking": [3, 0, 7, 1, ...]}}，数字是片段编号，从最相关到最不相关。

用户查询：{query}

候选片段：
{chr(10).join(items)}"""

    result = await _quick_llm(
        "你是文档相关性评分器。只返回JSON排名列表。",
        prompt,
        max_tokens=300,
    )

    if not result:
        return candidates[:top_k]

    try:
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(cleaned[start:end + 1])
            ranking = data.get("ranking", [])

            if isinstance(ranking, list) and ranking:
                reranked = []
                seen = set()
                for idx in ranking:
                    if isinstance(idx, int) and 0 <= idx < len(candidates):
                        if idx not in seen:
                            seen.add(idx)
                            reranked.append(candidates[idx])
                # Append any missed candidates
                for idx, cand in enumerate(candidates):
                    if idx not in seen:
                        reranked.append(cand)
                return reranked[:top_k]
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    return candidates[:top_k]


# ── RAG Pipeline ───────────────────────────────────────────────────────

async def rag_chat(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    top_k_docs: int = 20,
    top_k_questions: int = 5,
    enable_rewrite: bool = True,
    enable_rerank: bool = True,
    enable_self_rag: bool = True,
) -> Dict[str, Any]:
    """Advanced RAG chat with 5 optimization layers."""
    store = get_vector_store()
    started = time.perf_counter()
    optimization_log: List[str] = []

    # ── Layer 5: Self-RAG ──
    if enable_self_rag:
        do_retrieve = await should_retrieve(message, history)
        if not do_retrieve:
            optimization_log.append("self_rag:skip_retrieval")
            # Direct chat without retrieval
            return await _direct_chat(message, history, started)

    # ── Layer 3: Query Rewrite ──
    search_query = message
    sub_queries: List[str] = []
    if enable_rewrite:
        rewritten, sub_qs = await rewrite_query(message)
        if rewritten != message:
            optimization_log.append(f"rewrite:{message[:20]}->{rewritten[:20]}")
            search_query = rewritten
            sub_queries = sub_qs

    # ── Layer 1: Hybrid Search (TF-IDF + BM25 + RRF) ──
    # Search with main query
    search_results = store.search_all(
        search_query, doc_top_k=top_k_docs, question_top_k=top_k_questions
    )

    # Search with sub-queries and merge
    if sub_queries:
        from app.services.embedding_service import reciprocal_rank_fusion

        for sq in sub_queries:
            sub_results = store.search_all(sq, doc_top_k=10, question_top_k=3)
            # Merge via RRF
            fused_docs = reciprocal_rank_fusion(
                [(c, s) for c, s in search_results['documents']],
                [(c, s) for c, s in sub_results['documents']],
                k=60,
            )
            fused_qs = reciprocal_rank_fusion(
                [(c, s) for c, s in search_results['questions']],
                [(c, s) for c, s in sub_results['questions']],
                k=60,
            )
            search_results = {
                'documents': fused_docs[:top_k_docs],
                'questions': fused_qs[:top_k_questions],
            }

    optimization_log.append(
        f"retrieved:{len(search_results['documents'])}docs/"
        f"{len(search_results['questions'])}qs"
    )

    # ── Layer 2: Rerank ──
    if enable_rerank and len(search_results['documents']) > 5:
        search_results['documents'] = await rerank_chunks(
            message, search_results['documents'], top_k=5
        )
        search_results['questions'] = await rerank_chunks(
            message, search_results['questions'], top_k=3
        )
        optimization_log.append("rerank:applied")

    # ── Layer 4: Parent-Document context ──
    doc_context = _build_doc_context(search_results['documents'], use_parent=True)
    question_context = _build_question_context(search_results['questions'])

    optimization_log.append(
        f"parent_doc:{sum(1 for c,_ in search_results['documents'] if c.parent_text)}"
    )

    # ── Build prompt ──
    system_prompt = SYSTEM_PROMPT.format(
        doc_context=doc_context or "无相关文档片段",
        question_context=question_context or "无相关题目",
    )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for turn in history[-10:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    # ── Call LLM ──
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    context_used = len(search_results['documents']) > 0 or len(search_results['questions']) > 0
    sources = _extract_sources(search_results)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        reply = data["choices"][0]["message"]["content"]
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

        return {
            "reply": reply.strip(),
            "sources": sources,
            "context_used": context_used,
            "model": MODEL,
            "execution_time_ms": elapsed_ms,
            "optimizations": optimization_log,
        }

    except httpx.HTTPError as e:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "reply": f"AI服务暂时不可用（{type(e).__name__}），请稍后重试。",
            "sources": sources,
            "context_used": context_used,
            "model": None,
            "execution_time_ms": elapsed_ms,
            "error": str(e)[:200],
            "optimizations": optimization_log,
        }


async def _direct_chat(
    message: str,
    history: Optional[List[Dict[str, str]]],
    started: float,
) -> Dict[str, Any]:
    """Chat without retrieval (Self-RAG decided to skip)."""
    messages = [{
        "role": "system",
        "content": "你是人工智能训练师考试的智能助教。友好简洁地回答用户。如果不是考试相关问题，礼貌引导用户回到备考话题。"
    }]
    if history:
        for turn in history[-10:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 800,
        "temperature": 0.5,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        reply = data["choices"][0]["message"]["content"]
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "reply": reply.strip(),
            "sources": [],
            "context_used": False,
            "model": MODEL,
            "execution_time_ms": elapsed_ms,
            "optimizations": ["self_rag:direct_chat"],
        }
    except httpx.HTTPError as e:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "reply": f"AI服务暂时不可用（{type(e).__name__}）",
            "sources": [],
            "context_used": False,
            "model": None,
            "execution_time_ms": elapsed_ms,
            "error": str(e)[:200],
        }


async def rag_chat_stream(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    top_k_docs: int = 20,
    top_k_questions: int = 5,
) -> AsyncIterator[str]:
    """Streaming RAG chat with optimizations."""
    store = get_vector_store()

    # Self-RAG check
    if await should_retrieve(message, history):
        # Query rewrite
        search_query = message
        rewritten, sub_queries = await rewrite_query(message)
        if rewritten != message:
            search_query = rewritten

        # Hybrid search
        search_results = store.search_all(
            search_query, doc_top_k=top_k_docs, question_top_k=top_k_questions
        )

        # Rerank
        if len(search_results['documents']) > 5:
            search_results['documents'] = await rerank_chunks(
                message, search_results['documents'], top_k=5
            )

        doc_context = _build_doc_context(search_results['documents'], use_parent=True)
        question_context = _build_question_context(search_results['questions'])
        context_used = True
    else:
        search_results = {'documents': [], 'questions': []}
        doc_context = "无相关文档片段"
        question_context = "无相关题目"
        context_used = False

    system_prompt = SYSTEM_PROMPT.format(
        doc_context=doc_context, question_context=question_context
    )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for turn in history[-10:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.3,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        sources_json = json.dumps(_extract_sources(search_results), ensure_ascii=False)
                        yield f"data: [SOURCES]{sources_json}\n\n"
                        yield f"data: [DONE]\n\n"
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    except json.JSONDecodeError:
                        continue

    except httpx.HTTPError as e:
        yield f"data: {json.dumps({'error': str(e)[:200]})}\n\n"
        yield "data: [DONE]\n\n"


# ── Helpers ─────────────────────────────────────────────────────────────

def _build_doc_context(
    results: List[Tuple[DocumentChunk, float]],
    use_parent: bool = False,
) -> str:
    """Build document context string, optionally using parent chunks."""
    if not results:
        return ""
    lines = []
    for chunk, score in results[:5]:
        source = chunk.source or "未知来源"
        # Use parent_text if available and enabled
        context_text = chunk.parent_text if (use_parent and chunk.parent_text) else chunk.text
        lines.append(f"【来源: {source} (相关度: {score:.2f})】\n{context_text}")
    return "\n\n---\n\n".join(lines)


def _build_question_context(results: List[Tuple[DocumentChunk, float]]) -> str:
    """Build question context string."""
    if not results:
        return ""
    lines = []
    for chunk, score in results[:3]:
        lines.append(f"【相关度: {score:.2f}】\n{chunk.text}")
    return "\n\n---\n\n".join(lines)


def _extract_sources(
    search_results: Dict[str, List[Tuple[DocumentChunk, float]]]
) -> List[Dict[str, Any]]:
    """Extract source information from search results."""
    sources = []
    seen = set()

    for chunk, score in search_results.get('documents', []):
        if chunk.chunk_id not in seen:
            seen.add(chunk.chunk_id)
            sources.append({
                "chunk_id": chunk.chunk_id,
                "source": chunk.source,
                "relevance": round(score, 3),
                "excerpt": chunk.text[:200],
            })

    for chunk, score in search_results.get('questions', []):
        if chunk.chunk_id not in seen:
            seen.add(chunk.chunk_id)
            metadata = chunk.metadata or {}
            sources.append({
                "chunk_id": chunk.chunk_id,
                "source": chunk.source,
                "relevance": round(score, 3),
                "excerpt": chunk.text[:200],
                "question_id": metadata.get("question_id"),
                "question_type": metadata.get("type"),
            })

    sources.sort(key=lambda x: -x["relevance"])
    return sources[:8]
