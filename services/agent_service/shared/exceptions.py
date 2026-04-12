class RiteCareBaseException(Exception):
    """Base exception fro all RiteCare application errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

class ServiceUnavailableError(RiteCareBaseException):
    """Raised when downstram microservice is unreachable."""

class DocumentNotFoundError(RiteCareBaseException):
    """Raised when requested ocument does not exist in databse."""

class ValidationError(RiteCareBaseException):
    """Raised when input data fails business-level validation"""

class AgentError(RiteCareBaseException):
    """Raised when PydanticAI agent encounters an unrecoverable error."""