import re
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz
from app.models.vendor import Vendor


class VendorNormalizer:
    """Service for normalizing vendor names and maintaining vendor records."""

    def __init__(self, db: Session):
        self.db = db
        self.fuzzy_threshold = 85

        # Common vendor abbreviations and mappings
        self.vendor_map = {
            "AMZN": "Amazon",
            "AMAZON": "Amazon",
            "AMAZON.COM": "Amazon",
            "AWS": "Amazon Web Services",
            "AMAZON WEB SERVICES": "Amazon Web Services",
            "MSFT": "Microsoft",
            "MICROSOFT": "Microsoft",
            "MICROSOFT CORP": "Microsoft",
            "GOOG": "Google",
            "GOOGLE": "Google",
            "GOOGLE LLC": "Google",
            "GOOGLE CLOUD": "Google Cloud Platform",
            "GCP": "Google Cloud Platform",
            "AAPL": "Apple",
            "APPLE": "Apple",
            "APPLE INC": "Apple",
            "META": "Meta",
            "FACEBOOK": "Meta",
            "FB": "Meta",
        }

    def normalize(self, raw_name: str) -> str:
        """
        Normalize vendor name using exact match, fuzzy matching, and database lookup.

        Args:
            raw_name: Raw vendor name from invoice

        Returns:
            Normalized vendor name
        """
        if not raw_name:
            return "Unknown Vendor"

        # Clean the input
        clean = self._clean_name(raw_name)
        clean_upper = clean.upper()

        # Check exact match in vendor map
        if clean_upper in self.vendor_map:
            return self.vendor_map[clean_upper]

        # Check fuzzy match against known vendors
        fuzzy_match = self._fuzzy_match(clean_upper)
        if fuzzy_match:
            return fuzzy_match

        # Check database for existing normalized names
        db_match = self._find_in_database(clean)
        if db_match:
            return db_match

        # Return cleaned version if no match found
        return clean.title()

    def _clean_name(self, name: str) -> str:
        """Clean vendor name by removing special characters and extra whitespace."""
        # Remove common suffixes
        name = re.sub(r'\s+(INC|LLC|LTD|CORP|CO|CORPORATION|LIMITED)\.?$', '', name, flags=re.IGNORECASE)

        # Remove special characters except spaces and hyphens
        name = re.sub(r'[^\w\s-]', '', name)

        # Normalize whitespace
        name = ' '.join(name.split())

        return name.strip()

    def _fuzzy_match(self, clean_upper: str) -> Optional[str]:
        """Find fuzzy match in vendor map."""
        best_match = None
        best_score = 0

        for key, normalized in self.vendor_map.items():
            score = fuzz.ratio(clean_upper, key)
            if score > best_score and score >= self.fuzzy_threshold:
                best_score = score
                best_match = normalized

        return best_match

    def _find_in_database(self, clean_name: str) -> Optional[str]:
        """Check if similar vendor exists in database."""
        # Get all existing vendors
        vendors = self.db.query(Vendor).all()

        for vendor in vendors:
            # Check fuzzy match against existing normalized names
            if fuzz.ratio(clean_name.upper(), vendor.normalized_name.upper()) >= self.fuzzy_threshold:
                return vendor.normalized_name

        return None

    def update_vendor_stats(
        self,
        normalized_name: str,
        amount: Decimal,
        invoice_date: date
    ):
        """
        Update or create vendor record with aggregated statistics.

        Args:
            normalized_name: Normalized vendor name
            amount: Invoice amount to add
            invoice_date: Date of the invoice
        """
        vendor = self.db.query(Vendor).filter(
            Vendor.normalized_name == normalized_name
        ).first()

        if vendor:
            # Update existing vendor
            vendor.total_spent += amount
            vendor.invoice_count += 1

            # Update date range
            if invoice_date < vendor.first_seen:
                vendor.first_seen = invoice_date
            if invoice_date > vendor.last_seen:
                vendor.last_seen = invoice_date
        else:
            # Create new vendor
            vendor = Vendor(
                name=normalized_name,
                normalized_name=normalized_name,
                total_spent=amount,
                invoice_count=1,
                first_seen=invoice_date,
                last_seen=invoice_date,
                category=self._infer_category(normalized_name)
            )
            self.db.add(vendor)

        self.db.commit()

    def _infer_category(self, vendor_name: str) -> Optional[str]:
        """Infer vendor category based on name."""
        vendor_upper = vendor_name.upper()

        # Simple category inference
        if any(term in vendor_upper for term in ["AWS", "CLOUD", "AZURE", "GCP", "GOOGLE CLOUD"]):
            return "Cloud Services"
        elif any(term in vendor_upper for term in ["OFFICE", "MICROSOFT", "SOFTWARE"]):
            return "Software"
        elif any(term in vendor_upper for term in ["AMAZON", "SUPPLIES"]):
            return "Office Supplies"
        elif any(term in vendor_upper for term in ["TELECOM", "VERIZON", "AT&T", "PHONE"]):
            return "Telecommunications"
        else:
            return "Other"

    def add_mapping(self, abbreviation: str, normalized_name: str):
        """Add new vendor mapping to the normalization map."""
        self.vendor_map[abbreviation.upper()] = normalized_name
