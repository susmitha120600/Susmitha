from typing import List, Optional
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import EmbeddingError
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


class EmbeddingGenerator:
    
    def __init__(
        self,
        model: Optional[str] = None,
        batch_size: int = 100
    ):
        self.model = model or settings.EMBEDDING_MODEL
        self.batch_size = batch_size
        
        try:
            self.embeddings = OpenAIEmbeddings(
                model=self.model,
                openai_api_key=settings.OPENAI_API_KEY
            )
            logger.info(f"Initialized embedding generator with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {str(e)}")
            raise EmbeddingError("Failed to initialize embedding model", details={"error": str(e)})
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        if not documents:
            return []
        
        try:
            texts = [doc.page_content for doc in documents]
            
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(f"Embedded batch {i//self.batch_size + 1}/{(len(texts)-1)//self.batch_size + 1}")
            
            logger.info(f"Generated embeddings for {len(documents)} documents")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise EmbeddingError("Failed to generate embeddings", details={"error": str(e)})
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def embed_query(self, query: str) -> List[float]:
        try:
            embedding = self.embeddings.embed_query(query)
            logger.debug(f"Generated query embedding (dim={len(embedding)})")
            return embedding
        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise EmbeddingError("Failed to embed query", details={"error": str(e)})
    
    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def batch_similarity(
        self,
        query_embedding: List[float],
        document_embeddings: List[List[float]]
    ) -> List[float]:
        query_vec = np.array(query_embedding)
        doc_vecs = np.array(document_embeddings)
        
        dot_products = np.dot(doc_vecs, query_vec)
        query_norm = np.linalg.norm(query_vec)
        doc_norms = np.linalg.norm(doc_vecs, axis=1)
        
        similarities = dot_products / (doc_norms * query_norm)
        
        return similarities.tolist()
    
    def get_embedding_dimension(self) -> int:
        test_embedding = self.embed_query("test")
        return len(test_embedding)
