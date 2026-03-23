from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_TEMPERATURE: float = 0.0
    OPENAI_MAX_TOKENS: int = 2000
    
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"
    PINECONE_INDEX_NAME: str = "doc-intelligence"
    PINECONE_DIMENSION: int = 1536
    PINECONE_METRIC: str = "cosine"
    
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    MAX_CHUNK_SIZE: int = 1000
    MIN_CHUNK_SIZE: int = 100
    
    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANK: int = 5
    DENSE_WEIGHT: float = 0.7
    SPARSE_WEIGHT: float = 0.3
    USE_RERANKING: bool = True
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    MAX_CONTEXT_LENGTH: int = 4000
    CONTEXT_OPTIMIZATION: bool = True
    RECURSIVE_RETRIEVAL: bool = True
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = False
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    RAGAS_BATCH_SIZE: int = 10
    EVALUATION_DATASET_PATH: str = "data/evaluation/eval_dataset.json"
    
    PROJECT_NAME: str = "GenAI Document Intelligence Platform"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Production-ready RAG system with hybrid search and cross-encoder reranking"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
