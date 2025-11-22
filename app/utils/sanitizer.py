"""
Security utilities for sanitizing sensitive data in logs and error messages.

Prevents accidental exposure of:
- API keys, tokens, passwords
- Personal identifiable information (PII)
- Credit card numbers
- Internal system details
"""

import re
from typing import Any, Dict, List, Set
from copy import deepcopy


# Sensitive field patterns (case-insensitive)
SENSITIVE_KEYS: Set[str] = {
    # Authentication & Authorization
    'api_key', 'apikey', 'api-key',
    'auth_token', 'authtoken', 'auth-token',
    'access_token', 'accesstoken', 'access-token',
    'refresh_token', 'refreshtoken', 'refresh-token',
    'bearer_token', 'bearer',
    'secret', 'secret_key', 'secretkey',
    'private_key', 'privatekey', 'private-key',
    'password', 'passwd', 'pwd',
    'authorization', 'auth',

    # Payment & Financial
    'credit_card', 'creditcard', 'cc_number',
    'card_number', 'cvv', 'cvc', 'card_cvv',
    'account_number', 'routing_number',
    'ssn', 'social_security',

    # Personal Data
    'email', 'phone', 'phone_number',
    'address', 'street_address',
    'date_of_birth', 'dob',

    # Cookies & Sessions
    'cookie', 'session', 'session_id', 'sessionid',
    'csrf_token', 'csrftoken',

    # Database
    'connection_string', 'database_url', 'db_password',

    # Cloud/Infrastructure
    'aws_secret', 'aws_access_key',
    'gcp_key', 'azure_key',
}


# Regex patterns for sensitive data in text
SENSITIVE_PATTERNS: List[tuple] = [
    # API Keys (common formats)
    (re.compile(r'(?i)(api[_-]?key|apikey)[\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?'), 'API_KEY'),

    # Bearer tokens
    (re.compile(r'(?i)bearer\s+([a-zA-Z0-9_\-\.]{20,})'), 'BEARER_TOKEN'),

    # AWS keys
    (re.compile(r'AKIA[0-9A-Z]{16}'), 'AWS_ACCESS_KEY'),
    (re.compile(r'(?i)aws[_-]?secret[_-]?access[_-]?key[\s:=]+["\']?([a-zA-Z0-9/+=]{40})["\']?'), 'AWS_SECRET_KEY'),

    # Credit cards (basic pattern - matches most major cards)
    (re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'), 'CREDIT_CARD'),

    # Email addresses
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), 'EMAIL'),

    # Social Security Numbers
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), 'SSN'),

    # Phone numbers (US format)
    (re.compile(r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{4}\b'), 'PHONE'),

    # JWT tokens
    (re.compile(r'eyJ[a-zA-Z0-9_\-]*\.eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*'), 'JWT_TOKEN'),
]


def sanitize_dict(data: Dict[str, Any], redact_value: str = "***REDACTED***") -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary by redacting sensitive keys.

    Args:
        data: Dictionary to sanitize
        redact_value: String to replace sensitive values with

    Returns:
        Sanitized copy of the dictionary

    Example:
        >>> sanitize_dict({"api_key": "sk_live_123", "username": "john"})
        {"api_key": "***REDACTED***", "username": "john"}
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}

    for key, value in data.items():
        # Check if key is sensitive (case-insensitive)
        key_lower = key.lower().replace('-', '_')

        if key_lower in SENSITIVE_KEYS:
            sanitized[key] = redact_value
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = sanitize_dict(value, redact_value)
        elif isinstance(value, list):
            # Sanitize items in lists
            sanitized[key] = [
                sanitize_dict(item, redact_value) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def sanitize_string(text: str, redact_value: str = "***REDACTED***") -> str:
    """
    Sanitize a string by redacting sensitive patterns.

    Args:
        text: String to sanitize
        redact_value: String to replace sensitive values with

    Returns:
        Sanitized string

    Example:
        >>> sanitize_string("My API key is sk_live_1234567890")
        "My API key is ***REDACTED***"
    """
    if not isinstance(text, str):
        return text

    sanitized = text

    for pattern, label in SENSITIVE_PATTERNS:
        # Replace matched patterns with redacted value
        sanitized = pattern.sub(f'{redact_value}_{label}', sanitized)

    return sanitized


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize an exception message to remove sensitive data.

    Args:
        error: Exception to sanitize

    Returns:
        Sanitized error message

    Example:
        >>> err = Exception("API failed: token abc123xyz")
        >>> sanitize_error_message(err)
        "API failed: token ***REDACTED***"
    """
    error_msg = str(error)
    return sanitize_string(error_msg)


def sanitize_response_text(response_text: str, max_length: int = 500) -> str:
    """
    Sanitize API response text for safe logging.

    Args:
        response_text: Raw response text from API
        max_length: Maximum length to include in logs

    Returns:
        Sanitized and truncated response text

    Example:
        >>> sanitize_response_text("Error: invalid api_key sk_123")
        "Error: invalid api_key ***REDACTED***"
    """
    # First sanitize sensitive patterns
    sanitized = sanitize_string(response_text)

    # Truncate to prevent log flooding
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... [truncated]"

    return sanitized


def sanitize_url(url: str) -> str:
    """
    Sanitize URL by removing query parameters that might contain sensitive data.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL with sensitive query params redacted

    Example:
        >>> sanitize_url("https://api.example.com?api_key=secret123&user=john")
        "https://api.example.com?api_key=***REDACTED***&user=john"
    """
    import urllib.parse

    parsed = urllib.parse.urlparse(url)

    if not parsed.query:
        return url

    # Parse query parameters
    params = urllib.parse.parse_qs(parsed.query)

    # Sanitize sensitive parameters
    sanitized_params = {}
    for key, values in params.items():
        if key.lower().replace('-', '_') in SENSITIVE_KEYS:
            sanitized_params[key] = ['***REDACTED***'] * len(values)
        else:
            sanitized_params[key] = values

    # Rebuild URL
    new_query = urllib.parse.urlencode(sanitized_params, doseq=True)
    sanitized_url = urllib.parse.urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

    return sanitized_url


def is_sensitive_key(key: str) -> bool:
    """
    Check if a dictionary key is considered sensitive.

    Args:
        key: Key name to check

    Returns:
        True if key is sensitive, False otherwise

    Example:
        >>> is_sensitive_key("api_key")
        True
        >>> is_sensitive_key("username")
        False
    """
    return key.lower().replace('-', '_') in SENSITIVE_KEYS


# Export all sanitization functions
__all__ = [
    'sanitize_dict',
    'sanitize_string',
    'sanitize_error_message',
    'sanitize_response_text',
    'sanitize_url',
    'is_sensitive_key',
    'SENSITIVE_KEYS',
]
