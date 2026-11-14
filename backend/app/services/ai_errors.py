class ProviderUnavailableError(RuntimeError):
    """Raised when an external AI provider is not configured or reachable."""


class ProviderRequestError(RuntimeError):
    """Raised when an external AI provider rejects or cannot process a request."""
