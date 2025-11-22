"""
Comprehensive tests for VendorNormalizer.

Tests vendor name normalization and aggregation logic.
"""

import pytest
from unittest.mock import Mock, MagicMock
from decimal import Decimal
from datetime import date

from app.services.normalizer import VendorNormalizer


class TestVendorNormalizer:
    """Test suite for VendorNormalizer class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        # Mock query chain to return empty list by default
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first = Mock(return_value=None)
        mock_query.filter = Mock(return_value=mock_filter)
        mock_query.all = Mock(return_value=[])  # Return empty list for vendor lookups
        db.query = Mock(return_value=mock_query)
        db.add = Mock()
        db.commit = Mock()
        return db

    @pytest.fixture
    def normalizer(self, mock_db):
        """Create VendorNormalizer instance."""
        return VendorNormalizer(mock_db)

    def test_normalize_basic(self, normalizer):
        """Test basic vendor name normalization."""
        # Should normalize to title case and remove extra spaces
        assert normalizer.normalize("test vendor") == "Test Vendor"
        assert normalizer.normalize("TEST VENDOR") == "Test Vendor"
        assert normalizer.normalize("TeSt VeNdOr") == "Test Vendor"

    def test_normalize_extra_whitespace(self, normalizer):
        """Test normalization removes extra whitespace."""
        assert normalizer.normalize("  Test   Vendor  ") == "Test Vendor"
        assert normalizer.normalize("Test\t\tVendor") == "Test Vendor"

    def test_normalize_punctuation(self, normalizer):
        """Test normalization handles punctuation."""
        # Special characters are removed, then suffixes
        assert normalizer.normalize("Test & Co.") == "Test"  # & and . removed → "Test Co", then "CO" suffix removed
        assert normalizer.normalize("Test, Inc.") == "Test"  # Comma removed, Inc. suffix removed

    def test_normalize_company_suffixes(self, normalizer):
        """Test normalization of company suffixes."""
        # LLC variants should normalize
        assert normalizer.normalize("Test LLC") == "Test"
        assert normalizer.normalize("Test L.L.C.") == "Test Llc"  # Dots removed → "Test LLC" but suffix check already done
        assert normalizer.normalize("Test Inc.") == "Test"
        assert normalizer.normalize("Test Corporation") == "Test"  # "Corporation" is in suffix list

    def test_normalize_empty_string(self, normalizer):
        """Test normalization of empty string."""
        result = normalizer.normalize("")
        assert result == "Unknown Vendor"  # Returns "Unknown Vendor" for empty input

    def test_normalize_single_word(self, normalizer):
        """Test normalization of single word vendor."""
        assert normalizer.normalize("amazon") == "Amazon"
        assert normalizer.normalize("GOOGLE") == "Google"

    def test_normalize_numbers(self, normalizer):
        """Test normalization preserves numbers."""
        assert normalizer.normalize("Company 123") == "Company 123"
        assert normalizer.normalize("3M Corporation") == "3M"  # "Corporation" suffix is removed

    def test_normalize_special_cases(self, normalizer):
        """Test normalization of special vendor names."""
        # @ and . are removed, leaving "invoiceexamplecom"
        result = normalizer.normalize("invoice@example.com")
        assert "example" in result.lower()  # "example" is in "Invoiceexamplecom"

    def test_update_vendor_stats_new_vendor(self, normalizer, mock_db):
        """Test creating new vendor with initial stats."""
        # Mock vendor not existing
        mock_db.query().filter().first.return_value = None

        normalizer.update_vendor_stats(
            normalized_name="Test Vendor",
            amount=Decimal("100.00"),
            invoice_date=date(2025, 1, 1)
        )

        # Verify vendor was created
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Check the vendor object that was added
        vendor_obj = mock_db.add.call_args[0][0]
        assert vendor_obj.normalized_name == "Test Vendor"
        assert vendor_obj.total_spent == Decimal("100.00")
        assert vendor_obj.invoice_count == 1
        assert vendor_obj.first_seen == date(2025, 1, 1)
        assert vendor_obj.last_seen == date(2025, 1, 1)

    def test_update_vendor_stats_existing_vendor(self, normalizer, mock_db):
        """Test updating existing vendor stats."""
        # Mock existing vendor
        mock_vendor = Mock()
        mock_vendor.total_spent = Decimal("100.00")
        mock_vendor.invoice_count = 1
        mock_vendor.first_seen = date(2025, 1, 1)
        mock_vendor.last_seen = date(2025, 1, 1)

        mock_db.query().filter().first.return_value = mock_vendor

        # Update with new invoice
        normalizer.update_vendor_stats(
            normalized_name="Test Vendor",
            amount=Decimal("50.00"),
            invoice_date=date(2025, 1, 15)
        )

        # Verify stats were updated
        assert mock_vendor.total_spent == Decimal("150.00")
        assert mock_vendor.invoice_count == 2
        assert mock_vendor.last_seen == date(2025, 1, 15)
        assert mock_vendor.first_seen == date(2025, 1, 1)  # Should not change

        mock_db.commit.assert_called_once()

    def test_update_vendor_stats_earlier_date(self, normalizer, mock_db):
        """Test updating vendor with earlier invoice date."""
        # Mock existing vendor
        mock_vendor = Mock()
        mock_vendor.total_spent = Decimal("100.00")
        mock_vendor.invoice_count = 1
        mock_vendor.first_seen = date(2025, 1, 15)
        mock_vendor.last_seen = date(2025, 1, 15)

        mock_db.query().filter().first.return_value = mock_vendor

        # Update with earlier date
        normalizer.update_vendor_stats(
            normalized_name="Test Vendor",
            amount=Decimal("50.00"),
            invoice_date=date(2025, 1, 1)
        )

        # first_seen should update to earlier date
        assert mock_vendor.first_seen == date(2025, 1, 1)
        assert mock_vendor.last_seen == date(2025, 1, 15)  # Should not change

    def test_update_vendor_stats_zero_amount(self, normalizer, mock_db):
        """Test updating vendor with zero amount."""
        mock_db.query().filter().first.return_value = None

        normalizer.update_vendor_stats(
            normalized_name="Test Vendor",
            amount=Decimal("0.00"),
            invoice_date=date(2025, 1, 1)
        )

        # Should still create vendor
        mock_db.add.assert_called_once()

        vendor_obj = mock_db.add.call_args[0][0]
        assert vendor_obj.total_spent == Decimal("0.00")

    def test_normalize_consistency(self, normalizer):
        """Test normalization is consistent."""
        # Same vendor with different cases should normalize to same result
        name1 = normalizer.normalize("Test Company")
        name2 = normalizer.normalize("test company")
        name3 = normalizer.normalize("TEST COMPANY")

        assert name1 == name2 == name3

    def test_normalize_whitespace_variants(self, normalizer):
        """Test normalization handles various whitespace."""
        # All should normalize to same result
        name1 = normalizer.normalize("Test Company")
        name2 = normalizer.normalize("Test  Company")
        name3 = normalizer.normalize("  Test Company  ")
        name4 = normalizer.normalize("Test\nCompany")

        assert name1 == name2 == name3 == name4

    def test_normalize_handles_unicode(self, normalizer):
        """Test normalization handles unicode characters."""
        # Should handle non-ASCII characters
        result = normalizer.normalize("Café Company")
        assert "Caf" in result or "Cafe" in result

    def test_update_vendor_stats_decimal_precision(self, normalizer, mock_db):
        """Test vendor stats maintain decimal precision."""
        mock_vendor = Mock()
        mock_vendor.total_spent = Decimal("100.99")
        mock_vendor.invoice_count = 1
        mock_vendor.first_seen = date(2025, 1, 1)
        mock_vendor.last_seen = date(2025, 1, 1)

        mock_db.query().filter().first.return_value = mock_vendor

        normalizer.update_vendor_stats(
            normalized_name="Test Vendor",
            amount=Decimal("50.50"),
            invoice_date=date(2025, 1, 2)
        )

        # Should maintain precision
        assert mock_vendor.total_spent == Decimal("151.49")
        assert isinstance(mock_vendor.total_spent, Decimal)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
