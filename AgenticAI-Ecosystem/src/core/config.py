from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    MODEL_NAME: str = Field(default="gpt-4o", env="MODEL_NAME")
    TEMPERATURE: float = Field(default=0.1, env="TEMPERATURE")
    MAX_TOKENS: int = Field(default=4096, env="MAX_TOKENS")
    
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")
    EMBEDDING_DIMENSION: int = Field(default=3072, env="EMBEDDING_DIMENSION")
    
    VECTOR_DB_TYPE: str = Field(default="faiss", env="VECTOR_DB_TYPE")
    FAISS_INDEX_PATH: str = Field(default="./data/vectorstore/faiss_index", env="FAISS_INDEX_PATH")
    PINECONE_API_KEY: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME: Optional[str] = Field(default="agenticai", env="PINECONE_INDEX_NAME")
    
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/agenticai",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_TTL: int = Field(default=3600, env="REDIS_TTL")
    
    MAX_ITERATIONS: int = Field(default=3, env="MAX_ITERATIONS")
    QUALITY_THRESHOLD: float = Field(default=0.85, env="QUALITY_THRESHOLD")
    ENABLE_SELF_CORRECTION: bool = Field(default=True, env="ENABLE_SELF_CORRECTION")
    HALLUCINATION_THRESHOLD: float = Field(default=0.15, env="HALLUCINATION_THRESHOLD")
    CONFIDENCE_THRESHOLD: float = Field(default=0.75, env="CONFIDENCE_THRESHOLD")
    
    CHUNK_SIZE: int = Field(default=1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=200, env="CHUNK_OVERLAP")
    TOP_K_RETRIEVAL: int = Field(default=5, env="TOP_K_RETRIEVAL")
    RERANK_TOP_K: int = Field(default=3, env="RERANK_TOP_K")
    ENABLE_HYBRID_SEARCH: bool = Field(default=True, env="ENABLE_HYBRID_SEARCH")
    
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=4, env="API_WORKERS")
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE: str = Field(default="./logs/app.log", env="LOG_FILE")
    
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    LANGCHAIN_TRACING_V2: bool = Field(default=False, env="LANGCHAIN_TRACING_V2")
    LANGCHAIN_ENDPOINT: Optional[str] = Field(default=None, env="LANGCHAIN_ENDPOINT")
    LANGCHAIN_API_KEY: Optional[str] = Field(default=None, env="LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: Optional[str] = Field(default="agenticai-ecosystem", env="LANGCHAIN_PROJECT")
    
    SECRET_KEY: str = Field(default="change-me-in-production", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    @validator("VECTOR_DB_TYPE")
    def validate_vector_db_type(cls, v):
        allowed = ["faiss", "pinecone"]
        if v not in allowed:
            raise ValueError(f"VECTOR_DB_TYPE must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    def ensure_directories(self):
        directories = [
            Path(self.FAISS_INDEX_PATH).parent,
            Path(self.LOG_FILE).parent,
            Path("./data/documents"),
            Path("./data/database"),
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
settings.ensure_directories()
