class IntelForgeError(Exception):
    """Base application error."""


class ValidationError(IntelForgeError):
    """Raised when required input or a safety gate is invalid."""


class ProviderError(IntelForgeError):
    """Raised by a normalized external provider."""
