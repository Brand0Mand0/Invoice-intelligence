"""
JSON parsing utilities for handling AI model responses.

Provides robust parsing for JSON that may be wrapped in markdown code blocks
or mixed with explanatory text - common when working with LLM responses.
"""

import json
import re
from typing import Any, Dict, Optional


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from text that may contain markdown or other content.

    Handles common LLM response patterns:
    - JSON wrapped in markdown code blocks (```json ... ``` or ``` ... ```)
    - JSON embedded in explanatory text
    - Plain JSON

    Args:
        text: Text potentially containing JSON

    Returns:
        Parsed JSON as dictionary, or None if no valid JSON found

    Examples:
        >>> extract_json_from_text('{"key": "value"}')
        {'key': 'value'}

        >>> extract_json_from_text('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}

        >>> extract_json_from_text('Here is the data: {"key": "value"} - looks good!')
        {'key': 'value'}
    """
    if not text or not isinstance(text, str):
        return None

    # Strip whitespace
    text = text.strip()

    # Try 1: Remove markdown code blocks if present
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try 2: Extract JSON object if wrapped in text (find first { to last })
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try 3: Try parsing the entire string as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_yaml_from_text(text: str) -> Optional[str]:
    """
    Extract YAML from text that may contain markdown code blocks.

    Args:
        text: Text potentially containing YAML

    Returns:
        Extracted YAML string, or None if not found

    Examples:
        >>> extract_yaml_from_text('```yaml\\nkey: value\\n```')
        'key: value'

        >>> extract_yaml_from_text('key: value')
        'key: value'
    """
    if not text or not isinstance(text, str):
        return None

    # Strip whitespace
    text = text.strip()

    # Try removing markdown code blocks
    yaml_match = re.search(r'```(?:yaml|yml)?\s*(.*?)\s*```', text, re.DOTALL)
    if yaml_match:
        return yaml_match.group(1).strip()

    # If no code blocks, return as-is (might be plain YAML)
    return text


def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    Safely parse JSON with a default fallback value.

    Args:
        text: JSON string to parse
        default: Value to return if parsing fails (default: None)

    Returns:
        Parsed JSON or default value

    Examples:
        >>> safe_json_loads('{"key": "value"}')
        {'key': 'value'}

        >>> safe_json_loads('invalid json', default={})
        {}
    """
    if not text:
        return default

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def clean_json_string(text: str) -> str:
    """
    Clean and normalize JSON string for parsing.

    Removes:
    - Leading/trailing whitespace
    - Markdown code block markers
    - Common formatting issues

    Args:
        text: JSON string to clean

    Returns:
        Cleaned JSON string

    Examples:
        >>> clean_json_string('  ```json\\n{"key": "value"}\\n```  ')
        '{"key": "value"}'
    """
    if not text:
        return ""

    # Strip whitespace
    text = text.strip()

    # Remove markdown code blocks
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```', '', text)

    # Remove any leading/trailing quotes that might wrap the JSON
    text = text.strip('"\'')

    return text.strip()


def validate_json_structure(data: Dict[str, Any], required_keys: list) -> bool:
    """
    Validate that a JSON dictionary contains required keys.

    Args:
        data: Dictionary to validate
        required_keys: List of required key names

    Returns:
        True if all required keys present, False otherwise

    Examples:
        >>> validate_json_structure({"name": "John", "age": 30}, ["name", "age"])
        True

        >>> validate_json_structure({"name": "John"}, ["name", "age"])
        False
    """
    if not isinstance(data, dict):
        return False

    return all(key in data for key in required_keys)
