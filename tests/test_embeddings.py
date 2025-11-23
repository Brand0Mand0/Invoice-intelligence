"""Tests for embedding generation service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.embeddings import generate_embedding, generate_invoice_embedding
from app.models.invoice import Invoice
from datetime import date
from decimal import Decimal


class TestEmbeddingGeneration:
    """Test embedding generation with different providers."""

    @pytest.mark.asyncio
    async def test_generate_embedding_bge_basic(self):
        """Test basic BGE embedding generation."""
        with patch('app.services.embeddings.settings') as mock_settings, \
             patch('app.services.embeddings._get_bge_model') as mock_model_getter:

            mock_settings.EMBEDDING_PROVIDER = "bge"

            # Mock BGE model
            mock_model = Mock()
            mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 1024)
            mock_model_getter.return_value = mock_model

            result = await generate_embedding("test invoice text")

            assert isinstance(result, list)
            assert len(result) == 1024
            assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_generate_embedding_with_query_prefix(self):
        """Test BGE embedding with query instruction prefix."""
        with patch('app.services.embeddings.settings') as mock_settings, \
             patch('app.services.embeddings._get_bge_model') as mock_model_getter:

            mock_settings.EMBEDDING_PROVIDER = "bge"

            mock_model = Mock()
            mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 1024)
            mock_model_getter.return_value = mock_model

            # Generate with is_query=True
            await generate_embedding("search query", is_query=True)

            # Verify the model was called with prefixed text
            call_args = mock_model.encode.call_args[0][0]
            assert call_args.startswith("Represent this sentence for searching relevant passages:")
            assert "search query" in call_args

    @pytest.mark.asyncio
    async def test_generate_embedding_without_query_prefix(self):
        """Test BGE embedding without query prefix (document mode)."""
        with patch('app.services.embeddings.settings') as mock_settings, \
             patch('app.services.embeddings._get_bge_model') as mock_model_getter:

            mock_settings.EMBEDDING_PROVIDER = "bge"

            mock_model = Mock()
            mock_model.encode.return_value = Mock(tolist=lambda: [0.1] * 1024)
            mock_model_getter.return_value = mock_model

            # Generate with is_query=False (default)
            await generate_embedding("invoice document text", is_query=False)

            # Verify the model was called with original text (no prefix)
            call_args = mock_model.encode.call_args[0][0]
            assert call_args == "invoice document text"
            assert not call_args.startswith("Represent this sentence")

    @pytest.mark.asyncio
    async def test_generate_embedding_bge_model_unavailable(self):
        """Test error handling when BGE model is unavailable."""
        with patch('app.services.embeddings.settings') as mock_settings, \
             patch('app.services.embeddings._get_bge_model') as mock_model_getter:

            mock_settings.EMBEDDING_PROVIDER = "bge"
            mock_model_getter.return_value = None  # Model unavailable

            with pytest.raises(Exception, match="BGE model not available"):
                await generate_embedding("test text")

    @pytest.mark.asyncio
    async def test_generate_embedding_openai(self):
        """Test OpenAI embedding generation."""
        with patch('app.services.embeddings.settings') as mock_settings, \
             patch('httpx.AsyncClient') as mock_client:

            mock_settings.EMBEDDING_PROVIDER = "openai"
            mock_settings.OPENAI_API_KEY = "test-key"

            # Mock OpenAI API response
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.2] * 1024}]
            }
            mock_response.raise_for_status = Mock()

            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value.post.return_value = mock_response
            mock_client.return_value = mock_client_instance

            result = await generate_embedding("test text")

            assert isinstance(result, list)
            assert len(result) == 1024

    @pytest.mark.asyncio
    async def test_generate_embedding_unknown_provider(self):
        """Test error handling for unknown provider."""
        with patch('app.services.embeddings.settings') as mock_settings:
            mock_settings.EMBEDDING_PROVIDER = "unknown_provider"

            with pytest.raises(ValueError, match="Unknown embedding provider"):
                await generate_embedding("test text")


class TestInvoiceEmbedding:
    """Test invoice-specific embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_invoice_embedding(self):
        """Test generating embedding from invoice object."""
        # Create a mock invoice
        invoice = Invoice(
            vendor_name="Test Vendor Inc.",
            vendor_normalized="Test Vendor",
            invoice_number="INV-123",
            date=date(2025, 1, 15),
            total_amount=Decimal("99.99"),
            category="Software/SaaS",
            purchaser="John Doe",
            is_recurring=True,
            pdf_path="/tmp/test.pdf",
            pdf_hash="test_hash",
            parser_used="test",
            confidence_score=0.95
        )

        with patch('app.services.embeddings.generate_embedding') as mock_generate:
            mock_generate.return_value = [0.1] * 1024

            result = await generate_invoice_embedding(invoice)

            # Verify embedding was generated
            assert result == [0.1] * 1024

            # Verify the text representation included key fields
            call_args = mock_generate.call_args[0][0]
            assert "Test Vendor" in call_args
            assert "Software/SaaS" in call_args
            assert "99.99" in call_args
            assert "INV-123" in call_args
            assert "John Doe" in call_args
            assert "Yes" in call_args  # is_recurring

    @pytest.mark.asyncio
    async def test_generate_invoice_embedding_optional_fields(self):
        """Test embedding generation with missing optional fields."""
        # Create invoice with minimal fields
        invoice = Invoice(
            vendor_name="Basic Vendor",
            vendor_normalized="Basic Vendor",
            date=date(2025, 1, 1),
            total_amount=Decimal("50.00"),
            category="Other",
            pdf_path="/tmp/test.pdf",
            pdf_hash="hash",
            parser_used="test"
        )

        with patch('app.services.embeddings.generate_embedding') as mock_generate:
            mock_generate.return_value = [0.1] * 1024

            result = await generate_invoice_embedding(invoice)

            # Verify embedding was generated
            assert result == [0.1] * 1024

            # Verify the text handles None values
            call_args = mock_generate.call_args[0][0]
            assert "N/A" in call_args  # For invoice_number
            assert "N/A" in call_args  # For purchaser


class TestBGEModelLoading:
    """Test BGE model singleton and loading behavior."""

    def test_bge_model_singleton(self):
        """Test that BGE model is loaded once and cached."""
        with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
            from app.services.embeddings import _get_bge_model

            # Reset global state
            import app.services.embeddings
            app.services.embeddings._model = None

            mock_model = Mock()
            mock_transformer.return_value = mock_model

            # First call should load model
            result1 = _get_bge_model()
            assert result1 == mock_model
            assert mock_transformer.call_count == 1

            # Second call should return cached model
            result2 = _get_bge_model()
            assert result2 == mock_model
            assert mock_transformer.call_count == 1  # Not called again

    def test_bge_model_load_failure(self):
        """Test graceful handling when BGE model fails to load."""
        with patch('sentence_transformers.SentenceTransformer') as mock_transformer, \
             patch('app.services.embeddings.logger'):

            # Reset global state
            import app.services.embeddings
            app.services.embeddings._model = None

            # Simulate load failure
            mock_transformer.side_effect = Exception("Model download failed")

            from app.services.embeddings import _get_bge_model

            result = _get_bge_model()

            # Should return None and set sentinel value
            assert result is None

            # Second call should not retry (sentinel prevents retry loop)
            result2 = _get_bge_model()
            assert result2 is None
            assert mock_transformer.call_count == 1  # Only tried once
