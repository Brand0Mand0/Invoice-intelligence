import base64
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.config import get_settings
from app.core.constants import (
    NEAR_AI_TIMEOUT_SECONDS,
    AI_TEMPERATURE_EXTRACTION,
    AI_TEMPERATURE_TEMPLATE_GENERATION,
    AI_TEMPERATURE_CHAT,
    AI_MAX_TOKENS_EXTRACTION,
    AI_MAX_TOKENS_TEMPLATE,
    AI_MAX_TOKENS_CHAT,
    CHAT_CONTEXT_MAX_RECENT_INVOICES,
    CHAT_CONTEXT_TOP_VENDORS,
    DEFAULT_CHAT_HISTORY_LIMIT
)
from app.utils.json_parser import extract_json_from_text, extract_yaml_from_text
from app.models.invoice import Invoice
from app.models.vendor import Vendor
from app.services.base_api_client import BaseAPIClient
from app.core.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)


class NearAIService(BaseAPIClient):
    """Service for interacting with NEAR AI Cloud (DeepSeek and GLM-4.6)."""

    def __init__(self):
        super().__init__(
            base_url=settings.NEAR_AI_BASE_URL,
            api_key=settings.NEAR_AI_API_KEY,
            timeout=NEAR_AI_TIMEOUT_SECONDS
        )

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF file using pdfplumber.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text from all pages

        Raises:
            Exception: If no text could be extracted
        """
        import pdfplumber

        pdf_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pdf_text += page_text + "\n\n"

        if not pdf_text.strip():
            raise Exception("Could not extract text from PDF - may need OCR")

        return pdf_text

    def _build_extraction_prompt(self, pdf_text: str) -> str:
        """
        Build the extraction prompt for NEAR AI.

        Args:
            pdf_text: Extracted text from PDF

        Returns:
            Formatted prompt string
        """
        return f"""Extract invoice information from this text and return ONLY a valid JSON object with no additional text or markdown.

Invoice Text:
{pdf_text}

Return ONLY this JSON format (no explanations, no markdown):
{{
    "vendor": "vendor name here",
    "invoice_number": "invoice number or null",
    "date": "MM/DD/YYYY or null",
    "total_amount": 0.00,
    "category": "category here",
    "purchaser": "purchaser name or null",
    "is_recurring": false,
    "line_items": []
}}

Extract:
- vendor: Company/business name from top of invoice
- invoice_number: Invoice/order/receipt number
- date: Date in MM/DD/YYYY format
- total_amount: Total amount as number
- purchaser: Name of person/entity who made the purchase if shown on invoice, otherwise null
- category: Classify into ONE of these categories based on vendor and line items:
  * "Software/SaaS" - software licenses, subscriptions, cloud services, APIs
  * "Office Supplies" - paper, pens, supplies, furniture
  * "Marketing/Advertising" - ads, campaigns, social media, SEO
  * "Professional Services" - legal, accounting, consulting, freelancers
  * "Travel & Entertainment" - flights, hotels, meals, events
  * "Utilities" - internet, phone, electricity, water
  * "Equipment/Hardware" - computers, servers, devices
  * "Insurance" - health, business, liability insurance
  * "Rent/Facilities" - office rent, coworking, storage
  * "Payroll Services" - payroll processing, HR services
  * "Shipping/Fulfillment" - shipping, logistics, warehousing
  * "Other" - if none of the above fit
- is_recurring: true if this appears to be a subscription or recurring charge (monthly/annual), false otherwise
- line_items: Leave empty for now"""

    async def extract_invoice_data(self, pdf_path: str, model: str = "deepseek-ai/DeepSeek-V3.1") -> tuple[Dict[str, Any], str]:
        """
        Extract invoice data using NEAR AI models.
        This is the final fallback when invoice2data template matching fails.

        Args:
            pdf_path: Path to PDF file
            model: Model to use for extraction (default: DeepSeek-V3.1)

        Returns:
            Tuple of (extracted invoice data, model name used)
        """
        # Extract text from PDF
        pdf_text = self._extract_pdf_text(pdf_path)

        # Build extraction prompt
        prompt = self._build_extraction_prompt(pdf_text)

        # Call NEAR AI API using base client
        result = await self._post(
            "/v1/chat/completions",
            {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": AI_TEMPERATURE_EXTRACTION,
                "max_tokens": AI_MAX_TOKENS_EXTRACTION
            }
        )

        content = result["choices"][0]["message"]["content"].strip()

        # Parse JSON response using our utility
        extracted_data = extract_json_from_text(content)

        if not extracted_data:
            raise Exception(f"Could not parse JSON from AI response: {content[:200]}")

        return extracted_data, model

    async def generate_template_yaml(self, prompt: str) -> Optional[str]:
        """
        Generate invoice2data YAML template using NEAR AI.
        Used for auto-template generation after successful extraction.

        Args:
            prompt: Prompt describing the invoice and asking for template

        Returns:
            YAML template string or None if failed
        """
        try:
            # Call NEAR AI API using base client
            result = await self._post(
                "/v1/chat/completions",
                {
                    "model": "deepseek-ai/DeepSeek-V3.1",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": AI_TEMPERATURE_TEMPLATE_GENERATION,
                    "max_tokens": AI_MAX_TOKENS_TEMPLATE
                }
            )

            content = result["choices"][0]["message"]["content"].strip()

            # Extract YAML using utility (handles markdown blocks)
            yaml_content = extract_yaml_from_text(content)
            return yaml_content if yaml_content else ""

        except Exception as e:
            logger.error(
                "Template generation error",
                exc_info=True,
                extra={"extra_data": {"error": str(e)}}
            )
            return None

    async def chat(self, query: str, context: str) -> Dict[str, Any]:
        """
        Send chat query to NEAR AI GLM-4.6 model with database context.

        Args:
            query: User's natural language query
            context: Relevant database context

        Returns:
            Response with completion_id for TEE verification
        """
        system_prompt = f"""
        You are an AI assistant for an invoice intelligence platform.
        You have access to the following invoice and vendor data:

        {context}

        Answer the user's question based on this data. Be specific and provide numbers when relevant.
        If you cannot answer from the data provided, say so.
        """

        # Call NEAR AI API using base client
        result = await self._post(
            "/v1/chat/completions",
            {
                "model": "deepseek-ai/DeepSeek-V3.1",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": AI_TEMPERATURE_CHAT,
                "max_tokens": AI_MAX_TOKENS_CHAT
            }
        )

        return {
            "response": result["choices"][0]["message"]["content"],
            "model": "deepseek-ai/DeepSeek-V3.1",
            "completion_id": result.get("id")  # This is the chat completion ID for TEE verification
        }

    async def build_context(self, db: Session, query: str) -> str:
        """
        Build relevant context from database for chat query.

        Args:
            db: Database session
            query: User query to determine relevant context

        Returns:
            Formatted context string
        """
        context_parts = []

        # Get total statistics
        total_spent = db.query(func.sum(Invoice.total_amount)).scalar() or 0
        total_invoices = db.query(func.count(Invoice.id)).scalar() or 0
        total_vendors = db.query(func.count(Vendor.id)).scalar() or 0

        context_parts.append(f"Total Spent: ${total_spent:.2f}")
        context_parts.append(f"Total Invoices: {total_invoices}")
        context_parts.append(f"Total Vendors: {total_vendors}")

        # Get top vendors
        top_vendors = (
            db.query(Vendor)
            .order_by(Vendor.total_spent.desc())
            .limit(10)
            .all()
        )

        if top_vendors:
            context_parts.append("\nTop Vendors by Spending:")
            for vendor in top_vendors:
                context_parts.append(
                    f"- {vendor.normalized_name}: ${vendor.total_spent:.2f} "
                    f"({vendor.invoice_count} invoices)"
                )

        # Get recent invoices
        recent_invoices = (
            db.query(Invoice)
            .order_by(Invoice.date.desc())
            .limit(20)
            .all()
        )

        if recent_invoices:
            context_parts.append("\nRecent Invoices:")
            for inv in recent_invoices[:5]:
                context_parts.append(
                    f"- {inv.vendor_normalized}: ${inv.total_amount:.2f} "
                    f"on {inv.date}"
                )

        # If query mentions specific vendor, include their details
        query_lower = query.lower()
        for vendor in top_vendors:
            if vendor.normalized_name.lower() in query_lower:
                vendor_invoices = (
                    db.query(Invoice)
                    .filter(Invoice.vendor_normalized == vendor.normalized_name)
                    .order_by(Invoice.date.desc())
                    .limit(10)
                    .all()
                )

                context_parts.append(f"\n{vendor.normalized_name} Details:")
                context_parts.append(f"Total Spent: ${vendor.total_spent:.2f}")
                context_parts.append(f"Invoice Count: {vendor.invoice_count}")
                context_parts.append(f"First Invoice: {vendor.first_seen}")
                context_parts.append(f"Last Invoice: {vendor.last_seen}")

                if vendor_invoices:
                    context_parts.append("Recent Invoices:")
                    for inv in vendor_invoices:
                        context_parts.append(
                            f"- {inv.date}: ${inv.total_amount:.2f} (Invoice: {inv.invoice_number})"
                        )

        return "\n".join(context_parts)
