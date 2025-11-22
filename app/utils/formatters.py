"""
Formatting utilities for currency, dates, and other common display formats.

Centralizes all formatting logic to eliminate duplication across the codebase.
"""

from decimal import Decimal
from datetime import datetime, date
from typing import Union, Optional


def format_currency(amount: Union[Decimal, float, int], include_symbol: bool = True) -> str:
    """
    Format a number as currency.

    Args:
        amount: The amount to format
        include_symbol: Whether to include $ symbol (default: True)

    Returns:
        Formatted currency string (e.g., "$1,234.56")

    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(1234.56, include_symbol=False)
        '1,234.56'
    """
    if amount is None:
        return "$0.00" if include_symbol else "0.00"

    try:
        float_amount = float(amount)
        formatted = f"{float_amount:,.2f}"
        return f"${formatted}" if include_symbol else formatted
    except (ValueError, TypeError):
        return "$0.00" if include_symbol else "0.00"


def format_date(date_obj: Union[date, datetime, str], format_string: str = "%m/%d/%Y") -> str:
    """
    Format a date object or string into a consistent format.

    Args:
        date_obj: Date object, datetime object, or ISO date string
        format_string: Output format (default: "MM/DD/YYYY")

    Returns:
        Formatted date string

    Examples:
        >>> format_date(datetime(2025, 11, 21))
        '11/21/2025'
        >>> format_date("2025-11-21")
        '11/21/2025'
    """
    if date_obj is None:
        return ""

    try:
        # If it's already a date/datetime object
        if isinstance(date_obj, (date, datetime)):
            return date_obj.strftime(format_string)

        # If it's a string, try to parse it
        if isinstance(date_obj, str):
            # Try parsing as ISO format first
            try:
                parsed = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
                return parsed.strftime(format_string)
            except ValueError:
                pass

            # Try other common formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    parsed = datetime.strptime(date_obj, fmt)
                    return parsed.strftime(format_string)
                except ValueError:
                    continue

        return str(date_obj)
    except Exception:
        return str(date_obj) if date_obj else ""


def format_percentage(value: Union[float, int], decimals: int = 1) -> str:
    """
    Format a number as a percentage.

    Args:
        value: The value to format (0.0 to 1.0)
        decimals: Number of decimal places (default: 1)

    Returns:
        Formatted percentage string (e.g., "45.5%")

    Examples:
        >>> format_percentage(0.455)
        '45.5%'
        >>> format_percentage(0.455, decimals=2)
        '45.50%'
    """
    if value is None:
        return "0.0%"

    try:
        percentage = float(value) * 100
        return f"{percentage:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0.0%"


def format_number(value: Union[float, int], decimals: int = 0) -> str:
    """
    Format a number with thousands separators.

    Args:
        value: The number to format
        decimals: Number of decimal places (default: 0)

    Returns:
        Formatted number string (e.g., "1,234")

    Examples:
        >>> format_number(1234)
        '1,234'
        >>> format_number(1234.5678, decimals=2)
        '1,234.57'
    """
    if value is None:
        return "0"

    try:
        float_value = float(value)
        if decimals == 0:
            return f"{int(float_value):,}"
        else:
            return f"{float_value:,.{decimals}f}"
    except (ValueError, TypeError):
        return "0"


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: The string to truncate
        max_length: Maximum length including suffix
        suffix: String to append when truncated (default: "...")

    Returns:
        Truncated string

    Examples:
        >>> truncate_string("This is a very long string", 15)
        'This is a ve...'
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted file size (e.g., "1.5 MB")

    Examples:
        >>> format_file_size(1536)
        '1.5 KB'
        >>> format_file_size(1572864)
        '1.5 MB'
    """
    if size_bytes is None or size_bytes < 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"
