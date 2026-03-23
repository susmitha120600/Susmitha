from typing import List, Optional
import openai
from openai import OpenAI
import numpy as np
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import EmbeddingGenerationError
from app.utils.metrics import track_time, llm_latency

logger = get_logger(__name__)


class EmbeddingService:
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.dimension = settings.PINECONE_DIMENSION
        logger.info(f"EmbeddingService initialized with model: {self.model}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        try:
            if not text or not text.strip():
                raise EmbeddingGenerationError("Cannot generate embedding for empty text")
            
            text = text.replace("\n", " ").strip()
            
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            
            embedding = response.data[0].embedding
            
            if len(embedding) != self.dimension:
                raise EmbeddingGenerationError(
                    f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding)}"
                )
            
            return embedding
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise EmbeddingGenerationError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            raise EmbeddingGenerationError(f"Failed to generate embedding: {str(e)}")
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        try:
            if not texts:
                return []
            
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                cleaned_batch = [text.replace("\n", " ").strip() for text in batch]
                
                response = self.client.embeddings.create(
                    input=cleaned_batch,
                    model=self.model
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
            return all_embeddings
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error in batch processing: {str(e)}")
            raise EmbeddingGenerationError(f"Batch embedding generation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Batch embedding error: {str(e)}")
            raise EmbeddingGenerationError(f"Failed to generate batch embeddings: {str(e)}")
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            similarity = dot_product / (norm_v1 * norm_v2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Cosine similarity calculation error: {str(e)}")
            return 0.0
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        try:
            vec = np.array(embedding)
            norm = np.linalg.norm(vec)
            
            if norm == 0:
                return embedding
            
            normalized = vec / norm
            return normalized.tolist()
            
        except Exception as e:
            logger.error(f"Embedding normalization error: {str(e)}")
            return embedding
