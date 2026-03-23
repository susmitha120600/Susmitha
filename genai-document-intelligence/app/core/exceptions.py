from typing import Any, Optional


class BaseAPIException(Exception):
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class DocumentProcessingError(BaseAPIException):
    
    def __init__(self, message: str = "Error processing document", details: Optional[Any] = None):
        super().__init__(message, status_code=400, details=details)


class EmbeddingGenerationError(BaseAPIException):
    
    def __init__(self, message: str = "Error generating embeddings", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class VectorStoreError(BaseAPIException):
    
    def __init__(self, message: str = "Vector store operation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class RetrievalError(BaseAPIException):
    
    def __init__(self, message: str = "Error during retrieval", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class RerankingError(BaseAPIException):
    
    def __init__(self, message: str = "Error during reranking", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class RAGPipelineError(BaseAPIException):
    
    def __init__(self, message: str = "RAG pipeline error", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class EvaluationError(BaseAPIException):
    
    def __init__(self, message: str = "Evaluation error", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)


class ConfigurationError(BaseAPIException):
    
    def __init__(self, message: str = "Configuration error", details: Optional[Any] = None):
        super().__init__(message, status_code=500, details=details)
