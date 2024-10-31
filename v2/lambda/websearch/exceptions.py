class SearchError(Exception):
    """Base exception for search operations"""
    pass

class ConfigurationError(SearchError):
    """Raised when there's a configuration issue"""
    pass

class APIError(SearchError):
    """Raised when an API call fails"""
    pass
