"""Custom exceptions."""

class ResumeAIException(Exception):
    def __init__(self, message: str, error_code: str = 'INTERNAL_ERROR', status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(ResumeAIException):
    def __init__(self, message: str):
        super().__init__(message, error_code='VALIDATION_ERROR', status_code=400)

class FileProcessingError(ResumeAIException):
    def __init__(self, message: str):
        super().__init__(message, error_code='FILE_PROCESSING_ERROR', status_code=400)

class AIServiceError(ResumeAIException):
    def __init__(self, message: str):
        super().__init__(message, error_code='AI_SERVICE_ERROR', status_code=503)
