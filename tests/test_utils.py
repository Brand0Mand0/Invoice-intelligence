"""
Comprehensive tests for utility functions.

Tests formatters and JSON/YAML parsers.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime

from app.utils.formatters import (
    format_currency,
    format_date,
    format_percentage,
    format_number,
    truncate_string,
    format_file_size
)
from app.utils.json_parser import (
    extract_json_from_text,
    extract_yaml_from_text,
    validate_json_structure,
    clean_json_string
)


class TestFormatters:
    """Test suite for formatting utilities."""

    def test_format_currency_float(self):
        """Test currency formatting with float."""
        assert format_currency(1234.56) == "$1,234.56"
        assert format_currency(0.99) == "$0.99"
        assert format_currency(1000000.00) == "$1,000,000.00"

    def test_format_currency_decimal(self):
        """Test currency formatting with Decimal."""
        assert format_currency(Decimal("1234.56")) == "$1,234.56"
        assert format_currency(Decimal("0.99")) == "$0.99"

    def test_format_currency_int(self):
        """Test currency formatting with integer."""
        assert format_currency(1234) == "$1,234.00"
        assert format_currency(0) == "$0.00"

    def test_format_currency_none(self):
        """Test currency formatting with None."""
        assert format_currency(None) == "$0.00"

    def test_format_currency_without_symbol(self):
        """Test currency formatting without dollar sign."""
        assert format_currency(1234.56, include_symbol=False) == "1,234.56"

    def test_format_currency_invalid(self):
        """Test currency formatting with invalid input."""
        assert format_currency("invalid") == "$0.00"

    def test_format_date_date_object(self):
        """Test date formatting with date object."""
        test_date = date(2025, 1, 15)
        assert format_date(test_date) == "01/15/2025"

    def test_format_date_datetime_object(self):
        """Test date formatting with datetime object."""
        test_datetime = datetime(2025, 1, 15, 10, 30)
        assert format_date(test_datetime) == "01/15/2025"

    def test_format_date_custom_format(self):
        """Test date formatting with custom format string."""
        test_date = date(2025, 1, 15)
        assert format_date(test_date, format_string="%Y-%m-%d") == "2025-01-15"
        assert format_date(test_date, format_string="%d/%m/%Y") == "15/01/2025"

    def test_format_date_iso_string(self):
        """Test date formatting with ISO string."""
        assert format_date("2025-01-15") == "01/15/2025"

    def test_format_date_invalid(self):
        """Test date formatting with invalid input."""
        assert format_date("invalid") == "invalid"  # Returns str(date_obj) for unparseable strings
        assert format_date(None) == ""  # Returns empty string for None

    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(0.5) == "50.0%"
        assert format_percentage(0.123) == "12.3%"
        assert format_percentage(1.0) == "100.0%"

    def test_format_percentage_with_decimals(self):
        """Test percentage formatting with custom decimal places."""
        assert format_percentage(0.12345, decimals=2) == "12.35%"
        assert format_percentage(0.12345, decimals=4) == "12.3450%"

    def test_format_number(self):
        """Test number formatting with thousands separators."""
        assert format_number(1234567) == "1,234,567"
        assert format_number(1234.56) == "1,234"  # Default decimals=0 truncates to integer

    def test_format_number_with_decimals(self):
        """Test number formatting with specified decimal places."""
        assert format_number(1234.5678, decimals=2) == "1,234.57"
        assert format_number(1234, decimals=2) == "1,234.00"

    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(1073741824) == "1.0 GB"
        assert format_file_size(500) == "500.0 B"  # Uses "B" abbreviation with decimal

    def test_truncate_string(self):
        """Test string truncation."""
        long_string = "This is a very long string that needs to be truncated"
        assert truncate_string(long_string, 20) == "This is a very lo..."
        assert truncate_string(long_string, 100) == long_string

    def test_truncate_string_custom_suffix(self):
        """Test string truncation with custom suffix."""
        long_string = "This is a very long string"
        assert truncate_string(long_string, 10, suffix=">>>") == "This is>>>"


class TestJSONParser:
    """Test suite for JSON/YAML parsing utilities."""

    def test_extract_json_from_plain_text(self):
        """Test JSON extraction from plain JSON."""
        json_text = '{"vendor": "Test", "amount": 100}'
        result = extract_json_from_text(json_text)
        assert result == {"vendor": "Test", "amount": 100}

    def test_extract_json_from_markdown(self):
        """Test JSON extraction from markdown code block."""
        markdown_text = """Here's the data:
```json
{
    "vendor": "Test Company",
    "amount": 100.50
}
```
That's it!"""
        result = extract_json_from_text(markdown_text)
        assert result == {"vendor": "Test Company", "amount": 100.50}

    def test_extract_json_without_json_label(self):
        """Test JSON extraction from code block without 'json' label."""
        markdown_text = """```
{"vendor": "Test", "amount": 100}
```"""
        result = extract_json_from_text(markdown_text)
        assert result == {"vendor": "Test", "amount": 100}

    def test_extract_json_embedded_in_text(self):
        """Test JSON extraction when embedded in text."""
        text = 'The result is {"vendor": "Test", "amount": 100} as shown above.'
        result = extract_json_from_text(text)
        assert result == {"vendor": "Test", "amount": 100}

    def test_extract_json_invalid(self):
        """Test JSON extraction returns None for invalid JSON."""
        assert extract_json_from_text("not json at all") is None
        assert extract_json_from_text("") is None
        assert extract_json_from_text(None) is None

    def test_extract_yaml_from_plain_text(self):
        """Test YAML extraction from plain YAML."""
        yaml_text = """issuer: Test Company
invoice_number: INV-001
amount: 100.00"""
        result = extract_yaml_from_text(yaml_text)
        assert "issuer: Test Company" in result
        assert "amount: 100.00" in result

    def test_extract_yaml_from_markdown(self):
        """Test YAML extraction from markdown code block."""
        markdown_text = """Here's the template:
```yaml
issuer: Test Company
amount: 100.00
```"""
        result = extract_yaml_from_text(markdown_text)
        assert "issuer: Test Company" in result

    def test_extract_yaml_without_yaml_label(self):
        """Test YAML extraction from generic code block."""
        markdown_text = """```
issuer: Test
amount: 100
```"""
        result = extract_yaml_from_text(markdown_text)
        assert "issuer: Test" in result

    def test_validate_json_structure_valid(self):
        """Test JSON structure validation with valid data."""
        data = {
            "vendor": "Test",
            "amount": 100,
            "date": "2025-01-01"
        }
        required_fields = ["vendor", "amount"]
        assert validate_json_structure(data, required_fields) is True

    def test_validate_json_structure_missing_field(self):
        """Test JSON structure validation with missing field."""
        data = {"vendor": "Test"}
        required_fields = ["vendor", "amount"]
        assert validate_json_structure(data, required_fields) is False

    def test_validate_json_structure_none_data(self):
        """Test JSON structure validation with None."""
        assert validate_json_structure(None, ["vendor"]) is False

    def test_clean_json_string(self):
        """Test JSON string cleaning."""
        # Test with markdown code blocks
        dirty_json = '```json\n{"vendor": "Test"}\n```'
        clean = clean_json_string(dirty_json)
        assert clean == '{"vendor": "Test"}'

    def test_clean_json_string_with_whitespace(self):
        """Test JSON string cleaning with whitespace."""
        dirty_json = '  {"vendor": "Test"}  '
        clean = clean_json_string(dirty_json)
        assert clean == '{"vendor": "Test"}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
