from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    query: str = Field(..., description="The user query to process")
    use_rag: bool = Field(default=True, description="Enable RAG retrieval")
    use_sql: bool = Field(default=False, description="Enable SQL database queries")
    use_api: bool = Field(default=False, description="Enable external API calls")
    enable_self_correction: bool = Field(default=True, description="Enable self-correction loop")
    max_iterations: Optional[int] = Field(default=None, description="Maximum correction iterations")
    quality_threshold: Optional[float] = Field(default=None, description="Quality threshold for approval")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation memory")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the top selling products in Q4 2023?",
                "use_rag": True,
                "use_sql": True,
                "use_api": False,
                "enable_self_correction": True,
                "max_iterations": 3
            }
        }


class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the response")
    iterations: int = Field(..., description="Number of iterations performed")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: Optional[str] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on the database query results...",
                "metadata": {
                    "total_iterations": 2,
                    "final_score": 0.92,
                    "hallucination_score": 0.05,
                    "confidence": 0.88,
                    "sources": ["SQL Database", "Knowledge Base"],
                    "approved": True
                },
                "iterations": 2,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class DocumentIngestRequest(BaseModel):
    text: Optional[str] = Field(default=None, description="Raw text to ingest")
    file_path: Optional[str] = Field(default=None, description="Path to file to ingest")
    directory_path: Optional[str] = Field(default=None, description="Path to directory to ingest")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "directory_path": "./data/documents",
                "metadata": {"source": "company_docs", "date": "2024-01-01"}
            }
        }


class DocumentIngestResponse(BaseModel):
    success: bool
    message: str
    documents_processed: int
    chunks_created: int
    index_updated: bool


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    components: Dict[str, str]


class EvaluationRequest(BaseModel):
    query: str
    answer: str
    ground_truth: Optional[str] = Field(default=None)
    contexts: Optional[List[str]] = Field(default=None)


class EvaluationResponse(BaseModel):
    metrics: Dict[str, float]
    details: Dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = Field(default=None)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
