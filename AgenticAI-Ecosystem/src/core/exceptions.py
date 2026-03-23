class AgenticAIException(Exception):
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class AgentExecutionError(AgenticAIException):
    pass


class ToolExecutionError(AgenticAIException):
    pass


class RAGError(AgenticAIException):
    pass


class ValidationError(AgenticAIException):
    pass


class DatabaseError(AgenticAIException):
    pass


class EmbeddingError(AgenticAIException):
    pass


class ConfigurationError(AgenticAIException):
    pass
