class AppException(Exception):
    def __init__(self, code: int, message: str, detail: str | None = None):
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(message)


class AIServiceException(AppException):
    def __init__(self, message: str = "AI service unavailable", detail: str | None = None):
        super().__init__(503, message, detail)


class LLMException(AppException):
    def __init__(self, message: str = "LLM call failed", detail: str | None = None):
        super().__init__(502, message, detail)


class RAGException(AppException):
    def __init__(self, message: str = "RAG pipeline error", detail: str | None = None):
        super().__init__(500, message, detail)


class ToolException(AppException):
    def __init__(self, message: str = "Tool execution failed", detail: str | None = None):
        super().__init__(500, message, detail)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", detail: str | None = None):
        super().__init__(400, message, detail)
