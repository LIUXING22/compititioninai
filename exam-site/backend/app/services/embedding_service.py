"""
Hybrid vector store with TF-IDF + BM25 multi-retrieval and RRF fusion.
No external dependencies beyond Python stdlib.
"""
import math
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

from app.services.document_parser import DocumentChunk


# ── Chinese tokenization ─────────────────────────────────────────────

def tokenize_chinese(text: str) -> List[str]:
    """Tokenize Chinese text using character bigrams + single chars.

    Example: "机器学习" -> ["机器", "器学", "学习", "机", "器", "学", "习"]
    """
    cleaned = re.sub(r'[^一-鿿\w]', '', text)
    if not cleaned:
        return []

    tokens = []
    for i in range(len(cleaned) - 1):
        tokens.append(cleaned[i:i+2])
    for ch in cleaned:
        tokens.append(ch)

    return tokens


def tokenize_words(text: str) -> List[str]:
    """Tokenize text for BM25: keep alphanumeric words + Chinese bigrams."""
    cleaned = re.sub(r'[^一-鿿\w]', ' ', text)
    tokens = []
    # Extract continuous alpha/numeric sequences (keep as whole words)
    for word in re.findall(r'[a-zA-Z0-9]+', cleaned):
        tokens.append(word.lower())
    # Chinese bigrams
    cn = re.sub(r'[^一-鿿]', '', cleaned)
    for i in range(len(cn) - 1):
        tokens.append(cn[i:i+2])
    for ch in cn:
        tokens.append(ch)
    return tokens


# ── BM25 Retriever ───────────────────────────────────────────────────

class BM25Retriever:
    """Pure-Python BM25 retriever for keyword-precise matching."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[DocumentChunk] = []
        self.doc_terms: List[Dict[str, int]] = []    # term freq per doc
        self.doc_lengths: List[int] = []
        self.avgdl: float = 0.0
        self.doc_freq: Counter = Counter()
        self.total_docs: int = 0
        self.idf_cache: Dict[str, float] = {}

    def index(self, chunks: List[DocumentChunk]):
        """Build BM25 index from chunks."""
        for chunk in chunks:
            tokens = tokenize_words(chunk.text)
            term_counts = dict(Counter(tokens))
            self.doc_terms.append(term_counts)
            self.doc_lengths.append(len(tokens))
            for term in set(tokens):
                self.doc_freq[term] += 1
            self.chunks.append(chunk)

        self.total_docs = len(self.chunks)
        self.avgdl = sum(self.doc_lengths) / max(1, self.total_docs)

        # Precompute IDF
        self.idf_cache = {}
        for term, df in self.doc_freq.items():
            self.idf_cache[term] = math.log(
                (self.total_docs - df + 0.5) / (df + 0.5) + 1
            )

    def search(self, query: str, top_k: int = 20) -> List[Tuple[DocumentChunk, float]]:
        """BM25 search."""
        query_tokens = tokenize_words(query)
        if not query_tokens or self.total_docs == 0:
            return []

        scores: Dict[int, float] = {}
        for term in query_tokens:
            term_idf = self.idf_cache.get(term, 0)
            if term_idf == 0:
                continue
            for doc_idx, term_counts in enumerate(self.doc_terms):
                tf = term_counts.get(term, 0)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[doc_idx]
                bm25 = term_idf * (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                )
                scores[doc_idx] = scores.get(doc_idx, 0) + bm25

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [(self.chunks[idx], score) for idx, score in ranked[:top_k]]


# ── RRF Fusion ───────────────────────────────────────────────────────

def reciprocal_rank_fusion(
    *result_lists: List[Tuple[DocumentChunk, float]],
    k: int = 60,
) -> List[Tuple[DocumentChunk, float]]:
    """Fuse multiple ranked result lists using Reciprocal Rank Fusion."""
    scores: Dict[str, float] = {}
    chunk_map: Dict[str, DocumentChunk] = {}

    for result_list in result_lists:
        for rank, (chunk, _) in enumerate(result_list):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0) + 1.0 / (k + rank + 1)
            chunk_map[chunk.chunk_id] = chunk

    fused = sorted(scores.items(), key=lambda x: -x[1])
    return [(chunk_map[cid], score) for cid, score in fused]


# ── VectorStore (TF-IDF) ─────────────────────────────────────────────

class VectorStore:
    """In-memory TF-IDF vector store for document chunks."""

    OFFSET = 1000000

    def __init__(self):
        self.documents: List[DocumentChunk] = []
        self.question_docs: List[DocumentChunk] = []
        self.doc_freq: Counter = Counter()
        self.term_to_docs: Dict[str, List[int]] = defaultdict(list)
        self.doc_vectors: Dict[int, Dict[str, float]] = {}
        # Precomputed TF-IDF cache
        self._tfidf_cache: Dict[int, Dict[str, float]] = {}
        self._bm25: BM25Retriever | None = None
        self._all_chunks: List[DocumentChunk] = []

    def add_documents(self, chunks: List[DocumentChunk]):
        for chunk in chunks:
            self._add_single(chunk, is_question=False)

    def add_question_chunks(self, chunks: List[DocumentChunk]):
        for chunk in chunks:
            self._add_single(chunk, is_question=True)

    def _add_single(self, chunk: DocumentChunk, is_question: bool = False):
        doc_idx = len(self.documents) if not is_question else len(self.question_docs)
        tokens = tokenize_chinese(chunk.text)
        term_counts = Counter(tokens)

        for term in set(tokens):
            self.doc_freq[term] += 1
            self.term_to_docs[term].append(
                doc_idx if not is_question else doc_idx + self.OFFSET
            )

        key = doc_idx if not is_question else self.OFFSET + doc_idx
        self.doc_vectors[key] = dict(term_counts)

        if not is_question:
            self.documents.append(chunk)
        else:
            self.question_docs.append(chunk)

        self._all_chunks.append(chunk)

    def _build_bm25(self):
        """Lazily build BM25 index on first use."""
        if self._bm25 is None:
            self._bm25 = BM25Retriever()
            self._bm25.index(self.documents + self.question_docs)

    def _precompute_tfidf(self):
        """Precompute TF-IDF for all indexed documents (one-time)."""
        if self._tfidf_cache:
            return
        total_docs = len(self.documents) + len(self.question_docs)
        for key, counts in self.doc_vectors.items():
            self._tfidf_cache[key] = self._compute_tfidf(counts, total_docs)

    def _compute_tfidf(self, term_counts: Dict[str, int], total_docs: int) -> Dict[str, float]:
        tfidf = {}
        max_count = max(term_counts.values()) if term_counts else 0
        if max_count == 0:
            return tfidf
        for term, count in term_counts.items():
            tf = count / max_count
            df = self.doc_freq.get(term, 1)
            idf = math.log((total_docs + 1) / (df + 1)) + 1
            tfidf[term] = tf * idf
        return tfidf

    def _cosine_similarity(
        self, query_vector: Dict[str, float], doc_vector: Dict[str, float]
    ) -> float:
        if not query_vector or not doc_vector:
            return 0.0
        dot_product = sum(
            q_val * doc_vector.get(term, 0)
            for term, q_val in query_vector.items()
        )
        query_norm = math.sqrt(sum(v * v for v in query_vector.values()))
        doc_norm = math.sqrt(sum(v * v for v in doc_vector.values()))
        if query_norm == 0 or doc_norm == 0:
            return 0.0
        return dot_product / (query_norm * doc_norm)

    def _tfidf_search_internal(
        self, query: str, top_k: int = 20
    ) -> List[Tuple[DocumentChunk, float]]:
        """Internal TF-IDF search over all documents."""
        query_tokens = tokenize_chinese(query)
        if not query_tokens:
            return []

        self._precompute_tfidf()
        query_counts = Counter(query_tokens)
        total_docs = len(self.documents) + len(self.question_docs)
        query_vector = self._compute_tfidf(query_counts, total_docs)

        results = []
        for key, doc_vec in self._tfidf_cache.items():
            sim = self._cosine_similarity(query_vector, doc_vec)
            if sim > 0.001:
                if key >= self.OFFSET:
                    chunk = self.question_docs[key - self.OFFSET]
                else:
                    chunk = self.documents[key]
                results.append((chunk, sim))

        results.sort(key=lambda x: -x[1])
        return results[:top_k]

    def search(
        self, query: str, top_k: int = 20
    ) -> List[Tuple[DocumentChunk, float]]:
        """Hybrid search: TF-IDF + BM25 + RRF fusion."""
        self._build_bm25()

        # Dual-path retrieval
        tfidf_results = self._tfidf_search_internal(query, top_k=20)
        bm25_results = self._bm25.search(query, top_k=20)

        # RRF fusion
        fused = reciprocal_rank_fusion(tfidf_results, bm25_results, k=60)
        return fused[:top_k]

    def search_questions(
        self, query: str, top_k: int = 3
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search only question chunks (TF-IDF only for precision)."""
        self._precompute_tfidf()
        query_tokens = tokenize_chinese(query)
        if not query_tokens:
            return []

        query_counts = Counter(query_tokens)
        total_docs = len(self.documents) + len(self.question_docs)
        query_vector = self._compute_tfidf(query_counts, total_docs)

        results = []
        for i, chunk in enumerate(self.question_docs):
            key = self.OFFSET + i
            doc_vec = self._tfidf_cache.get(key, {})
            sim = self._cosine_similarity(query_vector, doc_vec)
            if sim > 0.001:
                results.append((chunk, sim))

        results.sort(key=lambda x: -x[1])
        return results[:top_k]

    def search_all(
        self, query: str, doc_top_k: int = 20, question_top_k: int = 3
    ) -> Dict[str, List[Tuple[DocumentChunk, float]]]:
        """Hybrid search both documents and questions."""
        return {
            'documents': self.search(query, top_k=doc_top_k),
            'questions': self.search_questions(query, top_k=question_top_k),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_documents': len(self.documents),
            'total_question_chunks': len(self.question_docs),
            'unique_terms': len(self.doc_freq),
            'indexed_sources': list(set(d.source for d in self.documents)),
            'bm25_enabled': self._bm25 is not None,
        }


# ── Singleton ───────────────────────────────────────────────────────

_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


def reset_vector_store():
    global _store
    _store = VectorStore()
