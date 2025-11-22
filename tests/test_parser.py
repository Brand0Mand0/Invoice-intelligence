"""
Comprehensive tests for PDF parser service.

Tests the PDFParser class including:
- File hash computation
- Cache lookup and storage
- Parser fallback chain
- Template generation
- Invoice validation
- Database operations
"""

import pytest
import hashlib
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, date
from decimal import Decimal

from app.services.parser import PDFParser
from app.core.constants import (
    CONFIDENCE_SCORE_TEMPLATE_MATCH,
    CONFIDENCE_SCORE_AI_EXTRACTION,
    FILE_HASH_CHUNK_SIZE
)


class TestPDFParser:
    """Test suite for PDFParser class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.flush = Mock()
        return db

    @pytest.fixture
    def parser(self, mock_db):
        """Create PDFParser instance with mock dependencies."""
        with patch('app.services.parser.VendorNormalizer'):
            with patch('app.services.parser.TemplateManager'):
                return PDFParser(mock_db)

    def test_compute_file_hash(self, parser, tmp_path):
        """Test SHA256 hash computation for PDF files."""
        # Create temporary test file
        test_file = tmp_path / "test.pdf"
        test_content = b"Test PDF content"
        test_file.write_bytes(test_content)

        # Compute hash
        file_hash = parser.compute_file_hash(str(test_file))

        # Verify hash is correct
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert file_hash == expected_hash
        assert len(file_hash) == 64  # SHA256 produces 64 hex characters

    def test_compute_file_hash_large_file(self, parser, tmp_path):
        """Test hash computation for large files using chunked reading."""
        # Create large test file (larger than FILE_HASH_CHUNK_SIZE)
        test_file = tmp_path / "large.pdf"
        test_content = b"x" * (FILE_HASH_CHUNK_SIZE * 3)
        test_file.write_bytes(test_content)

        # Compute hash
        file_hash = parser.compute_file_hash(str(test_file))

        # Verify hash is correct
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert file_hash == expected_hash

    @pytest.mark.asyncio
    async def test_process_with_cache_hit(self, parser, mock_db, tmp_path):
        """Test processing when cached result exists."""
        # Create temp PDF file
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"test pdf content")

        # Mock cached result
        cached_data = {
            "vendor": "Test Vendor",
            "invoice_number": "INV-001",
            "date": "01/01/2025",
            "total_amount": 100.00,
            "category": "Software/SaaS",
            "purchaser": None,
            "is_recurring": True,
            "line_items": []
        }

        mock_cache = Mock()
        mock_cache.extracted_data = cached_data
        mock_cache.parser_used = "invoice2data"
        mock_cache.confidence = CONFIDENCE_SCORE_TEMPLATE_MATCH

        mock_db.query().filter().first.return_value = mock_cache

        # Mock invoice save
        with patch.object(parser, '_save_invoice', new_callable=AsyncMock) as mock_save:
            mock_save.return_value = "test-invoice-id"

            # Process PDF (should use cache)
            result = await parser.process(str(test_pdf))

            # Verify cache was used
            assert result['invoice_id'] == "test-invoice-id"
            assert result['parser_used'] == "invoice2data"
            assert result['confidence'] == CONFIDENCE_SCORE_TEMPLATE_MATCH

    @pytest.mark.asyncio
    async def test_process_with_cache_miss_invoice2data_success(self, parser, mock_db, tmp_path):
        """Test processing with cache miss but invoice2data succeeds."""
        # Create temp PDF file
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"test pdf content")

        # No cache hit
        mock_db.query().filter().first.return_value = None

        # Mock invoice2data success
        extracted_data = {
            "vendor": "Test Vendor",
            "invoice_number": "INV-001",
            "date": "01/01/2025",
            "total_amount": 100.00,
            "category": "Software/SaaS",
            "purchaser": None,
            "is_recurring": False,
            "line_items": []
        }

        with patch.object(parser, '_parse_with_invoice2data', return_value=extracted_data):
            with patch.object(parser, '_validate_extraction', return_value=True):
                with patch.object(parser, '_save_invoice', new_callable=AsyncMock) as mock_save:
                    mock_save.return_value = "test-invoice-id"

                    # Process PDF
                    result = await parser.process(str(test_pdf))

                    # Verify invoice2data was used
                    assert result['parser_used'] == "invoice2data"
                    assert result['confidence'] == CONFIDENCE_SCORE_TEMPLATE_MATCH

                    # Verify cache was written
                    mock_db.add.assert_called()
                    mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_process_falls_back_to_near_ai(self, parser, mock_db, tmp_path):
        """Test fallback to NEAR AI when invoice2data fails."""
        # Create temp PDF file
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"test pdf content")

        # No cache hit
        mock_db.query().filter().first.return_value = None

        # Mock invoice2data failure
        with patch.object(parser, '_parse_with_invoice2data', return_value=None):
            # Mock NEAR AI success
            extracted_data = {
                "vendor": "Test Vendor",
                "invoice_number": "INV-002",
                "date": "01/02/2025",
                "total_amount": 200.00,
                "category": "Other",
                "purchaser": None,
                "is_recurring": False,
                "line_items": []
            }

            with patch('app.services.near_ai.NearAIService') as mock_near:
                mock_near_instance = Mock()
                mock_near_instance.extract_invoice_data = AsyncMock(
                    return_value=(extracted_data, "deepseek-ai/DeepSeek-V3.1")
                )
                mock_near.return_value = mock_near_instance

                with patch.object(parser, '_validate_extraction', return_value=True):
                    with patch.object(parser, '_generate_template', new_callable=AsyncMock):
                        with patch.object(parser, '_save_invoice', new_callable=AsyncMock) as mock_save:
                            mock_save.return_value = "test-invoice-id"

                            # Process PDF
                            result = await parser.process(str(test_pdf))

                            # Verify NEAR AI was used
                            assert result['parser_used'] == "deepseek-ai/DeepSeek-V3.1"
                            assert result['confidence'] == CONFIDENCE_SCORE_AI_EXTRACTION

    def test_validate_extraction_valid(self, parser):
        """Test validation of properly extracted data."""
        data = {
            "vendor": "Test Vendor",
            "total_amount": 100.00
        }

        assert parser._validate_extraction(data) is True

    def test_validate_extraction_missing_vendor(self, parser):
        """Test validation fails when vendor is missing."""
        data = {
            "vendor": "",
            "total_amount": 100.00
        }

        assert not parser._validate_extraction(data)  # Returns "" (falsy) not explicitly False

    def test_validate_extraction_zero_amount(self, parser):
        """Test validation fails when amount is zero."""
        data = {
            "vendor": "Test Vendor",
            "total_amount": 0
        }

        assert parser._validate_extraction(data) is False

    def test_validate_extraction_negative_amount(self, parser):
        """Test validation fails when amount is negative."""
        data = {
            "vendor": "Test Vendor",
            "total_amount": -50.00
        }

        assert parser._validate_extraction(data) is False

    def test_parse_date_string_various_formats(self, parser):
        """Test date parsing with different formats."""
        # Test MM/DD/YYYY
        date1 = parser._parse_date_string("01/15/2025")
        assert date1 == date(2025, 1, 15)

        # Test MM-DD-YYYY
        date2 = parser._parse_date_string("01-15-2025")
        assert date2 == date(2025, 1, 15)

        # Test YYYY-MM-DD
        date3 = parser._parse_date_string("2025-01-15")
        assert date3 == date(2025, 1, 15)

    def test_parse_date_string_invalid(self, parser):
        """Test date parsing returns None for invalid dates."""
        result = parser._parse_date_string("invalid-date")
        assert result is None

    def test_parse_date_string_empty(self, parser):
        """Test date parsing returns None for empty string."""
        result = parser._parse_date_string("")
        assert result is None

    def test_parse_with_invoice2data_success(self, parser, tmp_path):
        """Test successful invoice2data extraction."""
        # Create temp PDF file
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"test pdf content")

        with patch('invoice2data.extract_data') as mock_extract:
            # Mock invoice2data result
            mock_result = {
                "issuer": "Test Company",
                "invoice_number": "INV-123",
                "date": datetime(2025, 1, 1),
                "amount": Decimal("100.00"),
                "category": "Software/SaaS"
            }
            mock_extract.return_value = mock_result

            result = parser._parse_with_invoice2data(str(test_pdf))

            assert result is not None
            assert result['vendor'] == "Test Company"
            assert result['invoice_number'] == "INV-123"
            assert result['date'] == "01/01/2025"
            assert result['total_amount'] == 100.00
            assert result['category'] == "Software/SaaS"

    def test_parse_with_invoice2data_no_match(self, parser, tmp_path):
        """Test invoice2data returns None when no template matches."""
        # Create temp PDF file
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"test pdf content")

        with patch('invoice2data.extract_data') as mock_extract:
            mock_extract.return_value = None

            result = parser._parse_with_invoice2data(str(test_pdf))

            assert result is None

    @pytest.mark.asyncio
    async def test_save_invoice_creates_records(self, parser, mock_db):
        """Test invoice and line items are saved to database."""
        data = {
            "vendor": "Test Vendor",
            "vendor_normalized": "Test Vendor",
            "invoice_number": "INV-001",
            "date": "01/01/2025",
            "total_amount": 100.00,
            "category": "Software/SaaS",
            "purchaser": "John Doe",
            "is_recurring": True,
            "line_items": [
                {
                    "description": "Item 1",
                    "quantity": 1,
                    "unit_price": 50.00,
                    "total": 50.00
                },
                {
                    "description": "Item 2",
                    "quantity": 2,
                    "unit_price": 25.00,
                    "total": 50.00
                }
            ]
        }

        # Mock normalizer
        parser.normalizer.normalize = Mock(return_value="Test Vendor")
        parser.normalizer.update_vendor_stats = Mock()

        # Mock invoice ID after flush
        mock_invoice = Mock()
        mock_invoice.id = "test-invoice-id"
        parser.db.add = Mock(side_effect=lambda obj: setattr(obj, 'id', "test-invoice-id"))

        # Save invoice
        invoice_id = await parser._save_invoice(
            data=data,
            pdf_path="/path/to/test.pdf",
            pdf_hash="test-hash",
            parser_used="invoice2data",
            confidence=0.95
        )

        # Verify database operations
        assert invoice_id == "test-invoice-id"
        assert parser.db.add.call_count == 3  # 1 invoice + 2 line items
        parser.db.flush.assert_called_once()
        parser.db.commit.assert_called_once()
        parser.normalizer.update_vendor_stats.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
