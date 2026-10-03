import logging
import math
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from rank_bm25 import BM25Okapi

from backend.app.models.chunk import CodeChunk
from backend.app.rag.embeddings import embedding_service

logger = logging.getLogger(__name__)

class RetrievedCandidate:
    def __init__(
        self,
        chunk: CodeChunk,
        vector_score: float = 0.0,
        bm25_score: float = 0.0,
        hybrid_score: float = 0.0,
        vector_rank: Optional[int] = None,
        bm25_rank: Optional[int] = None,
    ):
        self.chunk = chunk
        self.vector_score = vector_score
        self.bm25_score = bm25_score
        self.hybrid_score = hybrid_score
        self.vector_rank = vector_rank
        self.bm25_rank = bm25_rank

class HybridRetriever:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def retrieve(
        self,
        query: str,
        repository_id: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k_vector: int = 20,
        top_k_bm25: int = 20,
        top_candidates: int = 35,
        alpha: float = 0.5, # Balance between vector (alpha) and BM25 (1 - alpha)
    ) -> List[RetrievedCandidate]:
        """
        Executes hybrid retrieval:
        1. Vector search
        2. BM25 keyword search
        3. Reciprocal Rank Fusion (RRF)
        """
        # Fetch candidate chunks from database according to repository and filters
        stmt = select(CodeChunk).where(CodeChunk.repository_id == repository_id)
        if filters:
            if filters.get("file_path"):
                stmt = stmt.where(CodeChunk.file_path.ilike(f"%{filters['file_path']}%"))
            if filters.get("language"):
                stmt = stmt.where(CodeChunk.language == filters["language"])
            if filters.get("symbol_type"):
                stmt = stmt.where(CodeChunk.symbol_type == filters["symbol_type"])
            if filters.get("chunk_type"):
                stmt = stmt.where(CodeChunk.chunk_type == filters["chunk_type"])

        result = await self.session.execute(stmt)
        chunks = list(result.scalars().all())

        if not chunks:
            logger.info(f"No chunks found for repository {repository_id}")
            return []

        # 1. Vector Search
        query_embedding = await embedding_service.get_embedding(query)
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)

        vector_scores: List[tuple[CodeChunk, float]] = []
        for ch in chunks:
            if ch.embedding:
                emb = ch.embedding if isinstance(ch.embedding, list) else list(ch.embedding)
                c_vec = np.array(emb, dtype=np.float32)
                c_norm = np.linalg.norm(c_vec)
                if q_norm > 0 and c_norm > 0:
                    sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
                else:
                    sim = 0.0
            else:
                sim = 0.0
            vector_scores.append((ch, sim))

        vector_scores.sort(key=lambda x: x[1], reverse=True)
        top_vector = vector_scores[:top_k_vector]

        # 2. BM25 Keyword Search
        tokenized_corpus = [
            f"{c.file_path} {c.symbol_name or ''} {c.content}".lower().split()
            for c in chunks
        ]
        bm25 = BM25Okapi(tokenized_corpus)
        query_tokens = query.lower().split()
        bm25_raw_scores = bm25.get_scores(query_tokens)

        bm25_scores: List[tuple[CodeChunk, float]] = [
            (chunks[i], float(bm25_raw_scores[i])) for i in range(len(chunks))
        ]
        bm25_scores.sort(key=lambda x: x[1], reverse=True)
        top_bm25 = bm25_scores[:top_k_bm25]

        # 3. Reciprocal Rank Fusion (RRF) & Merging
        # RRF formula: Score(d) = sum_{m in models} 1 / (k + rank_m(d)), k=60
        K_RRF = 60
        candidate_map: Dict[str, RetrievedCandidate] = {}

        # Record vector ranks
        for rank, (ch, v_score) in enumerate(top_vector, start=1):
            if ch.id not in candidate_map:
                candidate_map[ch.id] = RetrievedCandidate(chunk=ch)
            cand = candidate_map[ch.id]
            cand.vector_score = v_score
            cand.vector_rank = rank
            cand.hybrid_score += alpha * (1.0 / (K_RRF + rank))

        # Record BM25 ranks
        for rank, (ch, b_score) in enumerate(top_bm25, start=1):
            if ch.id not in candidate_map:
                candidate_map[ch.id] = RetrievedCandidate(chunk=ch)
            cand = candidate_map[ch.id]
            cand.bm25_score = b_score
            cand.bm25_rank = rank
            cand.hybrid_score += (1.0 - alpha) * (1.0 / (K_RRF + rank))

        merged_candidates = list(candidate_map.values())
        merged_candidates.sort(key=lambda c: c.hybrid_score, reverse=True)

        return merged_candidates[:top_candidates]
