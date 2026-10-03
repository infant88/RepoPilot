import re
from typing import List
from backend.app.rag.retriever import RetrievedCandidate
from backend.app.core.config import settings

class RerankedResult:
    def __init__(self, candidate: RetrievedCandidate, rerank_score: float, reasoning: str = ""):
        self.candidate = candidate
        self.chunk = candidate.chunk
        self.rerank_score = rerank_score
        self.reasoning = reasoning

class Reranker:
    def __init__(self):
        self.provider = settings.RERANKER_PROVIDER
        self.model_name = settings.RERANKER_MODEL

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedCandidate],
        top_k: int = 8
    ) -> List[RerankedResult]:
        """
        Reranks retrieved candidates using multi-factor cross-scoring:
        - Query-Code keyword and symbol intersection
        - Exact symbol name matching (function / class names in query)
        - File path relevance (e.g., matching modules mentioned in query)
        - Base hybrid retrieval score provenance
        """
        if not candidates:
            return []

        query_lower = query.lower()
        query_terms = set(re.findall(r"\w+", query_lower))
        
        # Identify high-value keywords like error codes or technical symbols
        status_codes = re.findall(r"\b[1-5]\d{2}\b", query) # 401, 500, etc.

        reranked: List[RerankedResult] = []

        for cand in candidates:
            chunk = cand.chunk
            content_lower = chunk.content.lower()
            path_lower = chunk.file_path.lower()
            symbol_lower = (chunk.symbol_name or "").lower()

            # Base normalized hybrid retrieval score (0.0 - 1.0 scale)
            base_score = cand.hybrid_score * 50.0  # Scale up RRF

            # 1. Exact symbol match bonus
            symbol_bonus = 0.0
            if chunk.symbol_name and any(term in symbol_lower for term in query_terms if len(term) > 3):
                symbol_bonus += 0.35

            # 2. File path relevance bonus
            path_bonus = 0.0
            for term in query_terms:
                if len(term) > 3 and term in path_lower:
                    path_bonus += 0.20

            # 3. HTTP status code or explicit error matching bonus (e.g. 401, 403, 404, 500)
            status_bonus = 0.0
            for code in status_codes:
                if code in content_lower:
                    status_bonus += 0.40

            # 4. Term density in chunk content
            content_terms = set(re.findall(r"\w+", content_lower))
            overlap = query_terms.intersection(content_terms)
            term_overlap_score = len(overlap) / max(len(query_terms), 1) * 0.30

            # 5. Penalize test files slightly if looking for implementation, unless query mentions tests
            test_penalty = 0.0
            if "test" in path_lower and "test" not in query_lower:
                test_penalty = 0.15

            final_score = base_score + symbol_bonus + path_bonus + status_bonus + term_overlap_score - test_penalty
            
            reason = (
                f"Base={base_score:.2f}, Sym={symbol_bonus:.2f}, "
                f"Path={path_bonus:.2f}, StatusMatch={status_bonus:.2f}"
            )
            reranked.append(RerankedResult(candidate=cand, rerank_score=final_score, reasoning=reason))

        reranked.sort(key=lambda x: x.rerank_score, reverse=True)
        return reranked[:top_k]

reranker_service = Reranker()
