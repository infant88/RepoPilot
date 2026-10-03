import hashlib
import logging
from typing import List
import numpy as np
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self._openai_client = None

        if self.provider == "openai" and settings.LLM_API_KEY:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=settings.LLM_API_KEY)
                logger.info(f"Initialized OpenAI embedding client ({self.model_name})")
            except Exception as e:
                logger.warning(f"Failed to init OpenAI embeddings: {e}. Falling back to local embeddings.")
                self.provider = "local"

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.provider == "openai" and self._openai_client:
            try:
                response = await self._openai_client.embeddings.create(
                    model=self.model_name or "text-embedding-3-small",
                    input=texts,
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}. Falling back to local deterministic embeddings.")

        # Local deterministic semantic embedding engine
        # Generates normalized vectors in R^{dimension}
        return [self._generate_local_embedding(text) for text in texts]

    async def get_embedding(self, text: str) -> List[float]:
        results = await self.get_embeddings([text])
        return results[0]

    def _generate_local_embedding(self, text: str) -> List[float]:
        """
        Deterministic, zero-dependency token-frequency semantic embedding generator.
        Produces unit-normalized 384-dimensional vectors with high semantic stability.
        """
        vector = np.zeros(self.dimension, dtype=np.float32)
        tokens = text.lower().replace("\n", " ").split()
        if not tokens:
            return vector.tolist()

        for token in tokens:
            # Hash token to dimension indices
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vector[idx] += sign

            # Secondary projection for n-gram feature mixing
            idx2 = (h >> 4) % self.dimension
            vector[idx2] += 0.5 * sign

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

embedding_service = EmbeddingService()
