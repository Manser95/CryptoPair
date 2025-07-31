"""Custom exceptions for the application"""


class RateLimitExceeded(Exception):
    """Raised when API rate limit is exceeded"""
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")


class ExternalAPIError(Exception):
    """Base exception for external API errors"""
    pass