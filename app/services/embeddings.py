"""Embeddings service with pluggable provider support (BGE-Large local by default)."""

from typing import List
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.models.invoice import Invoice

settings = get_settings()
logger = get_logger(__name__)

# Model singleton for BGE
_model = None


def _get_bge_model():
    """Load and cache BGE model with error handling."""
    global _model
    if _model is None:
        try:
            logger.info("Loading BGE-Large model (first time may download ~1.3GB from Hugging Face)...")
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('BAAI/bge-large-en-v1.5')
            logger.info("✅ BGE model loaded successfully (1024 dimensions)")
        except Exception as e:
            logger.error(
                "❌ Failed to load BGE model - embeddings disabled",
                exc_info=True,
                extra={"extra_data": {"error": str(e)}}
            )
            _model = False  # Sentinel value to stop retrying
    return _model if _model is not False else None


async def generate_embedding(text: str, is_query: bool = False) -> List[float]:
    """
    Generate embedding using configured provider.

    Args:
        text: Text to embed
        is_query: True if this is a search query (adds BGE instruction prefix for better accuracy)

    Providers:
    - "bge": BGE-Large (local, 1024-dim, FREE, private) - DEFAULT
    - "openai": OpenAI text-embedding-3-small (API, 1024-dim, $0.00002)
    """
    provider = settings.EMBEDDING_PROVIDER

    if provider == "bge":
        # Local BGE model
        model = _get_bge_model()
        if model is None:
            raise Exception("BGE model not available")

        # BGE performs ~5% better with instruction prefix for queries
        # See: https://huggingface.co/BAAI/bge-large-en-v1.5#using-huggingface-transformers
        if is_query:
            text = f"Represent this sentence for searching relevant passages: {text}"

        embedding = model.encode(text, convert_to_tensor=False)
        logger.debug(
            "Generated BGE embedding",
            extra={"extra_data": {"text_length": len(text), "dimensions": 1024}}
        )
        return embedding.tolist()

    elif provider == "openai":
        # OpenAI API with 1024 dimensions (using newer model)
        import httpx
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": text,
            "model": "text-embedding-3-small",  # Newer model, cheaper, configurable dims
            "dimensions": 1024  # Match BGE dimensions
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                embedding = result["data"][0]["embedding"]
                logger.debug(
                    "Generated OpenAI embedding",
                    extra={"extra_data": {"text_length": len(text), "dimensions": 1024}}
                )
                return embedding
        except Exception as e:
            logger.error(
                "OpenAI embedding failed",
                exc_info=True,
                extra={"extra_data": {"error": str(e)}}
            )
            raise Exception(f"Failed to generate OpenAI embedding: {str(e)}")

    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


async def generate_invoice_embedding(invoice: Invoice) -> List[float]:
    """
    Generate embedding for an invoice by combining key fields.

    Creates semantic representation that captures:
    - Vendor name and category
    - Amount and recurring status
    - Invoice metadata
    """
    text_representation = f"""
Invoice Information:
Vendor: {invoice.vendor_name} ({invoice.vendor_normalized})
Category: {invoice.category}
Amount: ${invoice.total_amount}
Date: {invoice.date}
Invoice Number: {invoice.invoice_number or 'N/A'}
Recurring: {'Yes' if invoice.is_recurring else 'No'}
Purchaser: {invoice.purchaser or 'N/A'}
""".strip()

    logger.debug(
        "Generating invoice embedding",
        extra={
            "extra_data": {
                "invoice_id": str(invoice.id),
                "vendor": invoice.vendor_normalized,
                "provider": settings.EMBEDDING_PROVIDER
            }
        }
    )

    return await generate_embedding(text_representation)
