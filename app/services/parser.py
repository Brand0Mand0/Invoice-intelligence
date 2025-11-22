import hashlib
import pdfplumber
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.invoice import Invoice, LineItem
from app.models.cache import ParseCache
from app.services.normalizer import VendorNormalizer
from app.services.template_manager import TemplateManager
from app.core.constants import (
    PARSER_VERSION,
    CONFIDENCE_SCORE_TEMPLATE_MATCH,
    CONFIDENCE_SCORE_AI_EXTRACTION,
    FILE_HASH_CHUNK_SIZE,
    TEMPLATE_GENERATION_MAX_TEXT_LENGTH,
    DATE_FORMATS,
    DEFAULT_CATEGORY
)
from app.core.logging_config import get_logger
import re

logger = get_logger(__name__)


class PDFParser:
    """Main PDF parsing service with fallback chain."""

    def __init__(self, db: Session):
        self.db = db
        self.normalizer = VendorNormalizer(db)
        self.parser_version = PARSER_VERSION

        # Initialize template manager and load templates
        self.template_manager = TemplateManager()
        self.custom_templates = self.template_manager.load_templates()

    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of PDF file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(FILE_HASH_CHUNK_SIZE), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def process(self, file_path: str) -> Dict[str, Any]:
        """
        Process PDF through extraction pipeline with fallback chain:
        1. Check cache
        2. Try pdfplumber
        3. Fallback to invoice2data
        4. Final fallback to NEAR AI
        """
        # Compute file hash for caching
        pdf_hash = self.compute_file_hash(file_path)
        cache_key = f"{pdf_hash}_{self.parser_version}"

        # Check cache first
        cached = self.db.query(ParseCache).filter(
            ParseCache.cache_key == cache_key
        ).first()

        if cached:
            extracted_data = cached.extracted_data
            parser_used = cached.parser_used
            confidence = cached.confidence
        else:
            # Try parsers in order
            extracted_data, parser_used, confidence = await self._try_parsers(file_path)

            # Convert Decimal to float for JSON serialization
            cache_data = extracted_data.copy()
            if 'total_amount' in cache_data and isinstance(cache_data['total_amount'], Decimal):
                cache_data['total_amount'] = float(cache_data['total_amount'])
            for item in cache_data.get('line_items', []):
                if 'quantity' in item and isinstance(item['quantity'], Decimal):
                    item['quantity'] = float(item['quantity'])
                if 'unit_price' in item and isinstance(item['unit_price'], Decimal):
                    item['unit_price'] = float(item['unit_price'])
                if 'total' in item and isinstance(item['total'], Decimal):
                    item['total'] = float(item['total'])

            # Cache the result
            cache_entry = ParseCache(
                cache_key=cache_key,
                extracted_data=cache_data,
                confidence=confidence,
                parser_used=parser_used
            )
            self.db.add(cache_entry)
            self.db.commit()

        # Save to database
        invoice_id = await self._save_invoice(
            extracted_data,
            file_path,
            pdf_hash,
            parser_used,
            confidence
        )

        return {
            "invoice_id": str(invoice_id),
            "parser_used": parser_used,
            "confidence": confidence,
            "vendor": extracted_data.get("vendor_normalized")
        }

    async def _try_parsers(self, file_path: str) -> tuple[Dict[str, Any], str, float]:
        """
        Try parsers in simplified fallback chain:
        1. invoice2data (template match - instant, 95% confidence)
        2. NEAR AI (intelligent extraction + auto-generates template for future, 95% confidence)

        pdfplumber removed - was unreliable (often extracted wrong vendor names)
        and added complexity without value. NEAR AI is only needed once per vendor.
        """
        # Try invoice2data first (instant if template exists)
        try:
            data = self._parse_with_invoice2data(file_path)
            if data and self._validate_extraction(data):
                logger.info(
                    "invoice2data matched template",
                    extra={"extra_data": {"vendor": data.get('vendor'), "parser": "invoice2data"}}
                )
                return data, "invoice2data", CONFIDENCE_SCORE_TEMPLATE_MATCH
        except Exception as e:
            logger.debug(
                "invoice2data failed (no template match)",
                extra={"extra_data": {"error": str(e)}}
            )

        # Fallback to NEAR AI (intelligent extraction + auto-template generation)
        try:
            from app.services.near_ai import NearAIService
            near_ai = NearAIService()
            data, model_used = await near_ai.extract_invoice_data(file_path)
            if data and self._validate_extraction(data):
                logger.info(
                    "NEAR AI extraction successful",
                    extra={"extra_data": {"vendor": data.get('vendor'), "model": model_used}}
                )

                # Auto-generate template for next time (self-improving system)
                await self._generate_template(file_path, data, near_ai)

                return data, model_used, CONFIDENCE_SCORE_AI_EXTRACTION
        except Exception as e:
            logger.error(
                "NEAR AI extraction failed",
                exc_info=True,
                extra={"extra_data": {"error": str(e)}}
            )
            raise Exception("Both invoice2data and NEAR AI parsers failed to extract invoice data")


    async def _generate_template(self, file_path: str, extracted_data: Dict[str, Any], near_ai):
        """
        Auto-generate invoice2data template using NEAR AI after successful extraction.
        This builds the template library automatically over time.
        """
        try:
            vendor_name = extracted_data.get("vendor", "").strip()
            if not vendor_name or vendor_name == "Unknown Vendor":
                logger.warning(
                    "Skipping template generation - no valid vendor name",
                    extra={"extra_data": {"vendor": vendor_name}}
                )
                return

            # Check if template already exists using TemplateManager
            if self.template_manager.template_exists(vendor_name):
                logger.debug(
                    "Template already exists for vendor",
                    extra={"extra_data": {"vendor": vendor_name}}
                )
                return

            # Extract full text from PDF
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n\n"

            if not full_text.strip():
                logger.warning(
                    "No text extracted from PDF - cannot generate template",
                    extra={"extra_data": {"vendor": vendor_name}}
                )
                return

            # Ask NEAR AI to generate template YAML
            prompt = f"""Analyze this invoice and create an invoice2data YAML template.

Invoice text:
{full_text[:TEMPLATE_GENERATION_MAX_TEXT_LENGTH]}

Extracted data:
- Vendor: {extracted_data.get('vendor')}
- Invoice Number: {extracted_data.get('invoice_number')}
- Date: {extracted_data.get('date')}
- Amount: {extracted_data.get('total_amount')}

Create a YAML template with:
- issuer: "{vendor_name}"
- fields: regex patterns for invoice_number, date, amount
- keywords: 3-5 unique keywords from this vendor's invoices
- options: currency and date_formats

Return ONLY valid YAML, no markdown or explanations."""

            template_yaml = await near_ai.generate_template_yaml(prompt)

            if template_yaml:
                # Save template using TemplateManager
                if self.template_manager.save_template(vendor_name, template_yaml):
                    # Reload templates
                    self.custom_templates = self.template_manager.load_templates()

        except Exception as e:
            logger.warning(
                "Template generation failed",
                exc_info=True,
                extra={"extra_data": {"vendor": vendor_name, "error": str(e)}}
            )
            # Don't raise - template generation is optional enhancement

    def _parse_with_invoice2data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract invoice data using invoice2data library with custom templates."""
        try:
            from invoice2data import extract_data

            # Try custom templates first, then fall back to built-in templates
            result = None

            # Try custom templates
            if self.custom_templates:
                result = extract_data(file_path, templates=self.custom_templates)

            # Fall back to built-in templates if custom didn't match
            if not result:
                result = extract_data(file_path)

            if result:
                # Handle date field (could be datetime or string)
                date_value = result.get("date", "")
                if hasattr(date_value, 'strftime'):
                    date_value = date_value.strftime("%m/%d/%Y")

                # Ensure amount is float, not Decimal
                amount = result.get("amount", 0)
                if isinstance(amount, Decimal):
                    amount = float(amount)

                return {
                    "vendor": result.get("issuer", ""),
                    "invoice_number": result.get("invoice_number", ""),
                    "date": date_value,
                    "total_amount": amount,
                    "category": result.get("category", DEFAULT_CATEGORY),  # Templates can optionally specify category
                    "purchaser": result.get("purchaser"),  # None if not specified in template
                    "is_recurring": result.get("is_recurring", False),  # Templates can mark as recurring
                    "line_items": []
                }
        except Exception as e:
            logger.debug(
                "invoice2data extraction error",
                extra={"extra_data": {"error": str(e)}}
            )
            return None

    def _validate_extraction(self, data: Dict[str, Any]) -> bool:
        """Validate that extracted data has minimum required fields."""
        return (
            data.get("vendor") and
            data.get("total_amount") is not None and
            data.get("total_amount") > 0
        )

    async def _save_invoice(
        self,
        data: Dict[str, Any],
        pdf_path: str,
        pdf_hash: str,
        parser_used: str,
        confidence: float
    ) -> str:
        """Save extracted invoice data to database."""
        # Normalize vendor
        vendor_normalized = self.normalizer.normalize(data["vendor"])

        # Parse date
        invoice_date = self._parse_date_string(data.get("date")) or datetime.now().date()

        # Ensure total_amount is Decimal (could be float from invoice2data or Decimal from pdfplumber)
        total_amount = data["total_amount"]
        if not isinstance(total_amount, Decimal):
            total_amount = Decimal(str(total_amount))

        # Extract business intelligence fields
        category = data.get("category", DEFAULT_CATEGORY)
        purchaser = data.get("purchaser")  # None if not specified
        is_recurring = data.get("is_recurring", False)

        # Create invoice
        invoice = Invoice(
            vendor_name=data["vendor"],
            vendor_normalized=vendor_normalized,
            invoice_number=data.get("invoice_number"),
            date=invoice_date,
            total_amount=total_amount,
            category=category,
            purchaser=purchaser,
            is_recurring=is_recurring,
            pdf_path=pdf_path,
            pdf_hash=pdf_hash,
            confidence_score=confidence,
            parser_used=parser_used,
            parser_version=self.parser_version
        )

        self.db.add(invoice)
        self.db.flush()  # Get invoice ID

        # Add line items
        for item_data in data.get("line_items", []):
            line_item = LineItem(
                invoice_id=invoice.id,
                description=item_data["description"],
                quantity=item_data.get("quantity"),
                unit_price=item_data.get("unit_price"),
                total=item_data["total"]
            )
            self.db.add(line_item)

        # Update vendor aggregates
        self.normalizer.update_vendor_stats(
            vendor_normalized,
            total_amount,
            invoice_date
        )

        self.db.commit()
        return invoice.id

    def _parse_date_string(self, date_str: Optional[str]) -> Optional[datetime.date]:
        """Parse date string to date object."""
        if not date_str:
            return None

        # Try common formats from constants
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None
