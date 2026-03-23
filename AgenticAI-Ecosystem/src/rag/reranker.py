from typing import List, Tuple
from sentence_transformers import CrossEncoder
from langchain.schema import Document
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class CrossEncoderReranker:
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        try:
            self.model = CrossEncoder(model_name)
            logger.info(f"Initialized cross-encoder reranker: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize reranker: {str(e)}")
            raise
    
    def rerank(
        self,
        query: str,
        documents: List[Tuple[Document, float]],
        top_k: int = None
    ) -> List[Tuple[Document, float]]:
        if not documents:
            return []
        
        top_k = top_k or settings.RERANK_TOP_K
        
        try:
            query_doc_pairs = [
                [query, doc.page_content] for doc, _ in documents
            ]
            
            scores = self.model.predict(query_doc_pairs)
            
            reranked = [
                (doc, float(score))
                for (doc, _), score in zip(documents, scores)
            ]
            
            reranked.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Reranked {len(documents)} documents, returning top {top_k}")
            
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Error during reranking: {str(e)}")
            return documents[:top_k]
    
    def score_pairs(self, query: str, texts: List[str]) -> List[float]:
        pairs = [[query, text] for text in texts]
        scores = self.model.predict(pairs)
        return scores.tolist()
