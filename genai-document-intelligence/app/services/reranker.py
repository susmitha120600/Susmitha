from typing import List, Tuple
from sentence_transformers import CrossEncoder
import numpy as np
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import RerankingError
from app.models.schemas import SearchResult
from app.utils.metrics import track_time, reranking_latency

logger = get_logger(__name__)


class Reranker:
    
    def __init__(self):
        try:
            self.model_name = settings.RERANKER_MODEL
            logger.info(f"Loading cross-encoder model: {self.model_name}")
            
            self.model = CrossEncoder(self.model_name)
            
            logger.info("Reranker initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reranker: {str(e)}")
            raise RerankingError(f"Reranker initialization failed: {str(e)}")
    
    @track_time(reranking_latency)
    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 5
    ) -> List[SearchResult]:
        try:
            if not results:
                logger.warning("No results to rerank")
                return []
            
            if len(results) <= top_k:
                logger.info(f"Results count ({len(results)}) <= top_k ({top_k}), returning all")
                return results
            
            logger.info(f"Reranking {len(results)} results to top {top_k}")
            
            query_doc_pairs = [(query, result.text) for result in results]
            
            scores = self.model.predict(query_doc_pairs)
            
            result_score_pairs = list(zip(results, scores))
            result_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            reranked_results = []
            for idx, (result, score) in enumerate(result_score_pairs[:top_k]):
                reranked_result = SearchResult(
                    chunk_id=result.chunk_id,
                    text=result.text,
                    score=float(score),
                    source=result.source,
                    metadata={
                        **result.metadata,
                        "original_score": result.score,
                        "rerank_score": float(score),
                        "rerank_position": idx + 1
                    }
                )
                reranked_results.append(reranked_result)
            
            logger.info(f"Reranking complete, returned top {len(reranked_results)} results")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Reranking error: {str(e)}")
            raise RerankingError(f"Failed to rerank results: {str(e)}")
    
    async def score_pairs(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        try:
            if not texts:
                return []
            
            query_doc_pairs = [(query, text) for text in texts]
            
            scores = self.model.predict(query_doc_pairs)
            
            return [float(score) for score in scores]
            
        except Exception as e:
            logger.error(f"Scoring error: {str(e)}")
            raise RerankingError(f"Failed to score pairs: {str(e)}")
    
    def get_model_info(self) -> dict:
        return {
            "model_name": self.model_name,
            "model_type": "cross-encoder"
        }
