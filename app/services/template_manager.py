"""
Template manager for invoice2data templates.

Handles loading, saving, and managing invoice2data YAML templates
for automatic invoice extraction.
"""

import os
import re
from typing import List, Optional
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TemplateManager:
    """Manages invoice2data template files."""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize TemplateManager.

        Args:
            template_dir: Path to templates directory. If None, uses default app/templates
        """
        if template_dir is None:
            # Default to app/templates directory
            template_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "templates"
            )

        self.template_dir = template_dir

    def load_templates(self) -> List:
        """
        Load custom invoice2data templates from directory.

        Returns:
            List of template objects from invoice2data library
        """
        try:
            from invoice2data.extract.loader import read_templates

            if os.path.exists(self.template_dir):
                templates = read_templates(self.template_dir)
                logger.info(
                    "Loaded custom invoice2data templates",
                    extra={"extra_data": {"count": len(templates), "directory": self.template_dir}}
                )
                return templates
            else:
                logger.debug(
                    "No custom templates directory found",
                    extra={"extra_data": {"directory": self.template_dir}}
                )
                return []
        except Exception as e:
            logger.error(
                "Error loading custom templates",
                exc_info=True,
                extra={"extra_data": {"error": str(e)}}
            )
            return []

    def template_exists(self, vendor_name: str) -> bool:
        """
        Check if a template exists for a vendor.

        Args:
            vendor_name: Name of the vendor

        Returns:
            True if template file exists
        """
        if not vendor_name or vendor_name == "Unknown Vendor":
            return False

        template_filename = self._get_template_filename(vendor_name)
        template_path = os.path.join(self.template_dir, template_filename)
        return os.path.exists(template_path)

    def save_template(self, vendor_name: str, yaml_content: str) -> bool:
        """
        Save a template for a vendor.

        Args:
            vendor_name: Name of the vendor
            yaml_content: YAML template content

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not vendor_name or vendor_name == "Unknown Vendor":
                logger.warning(
                    "Invalid vendor name for template",
                    extra={"extra_data": {"vendor": vendor_name}}
                )
                return False

            template_filename = self._get_template_filename(vendor_name)
            template_path = os.path.join(self.template_dir, template_filename)

            # Ensure template directory exists
            os.makedirs(self.template_dir, exist_ok=True)

            # Save template
            with open(template_path, 'w') as f:
                f.write(yaml_content)

            logger.info(
                "Auto-generated template saved",
                extra={"extra_data": {"vendor": vendor_name, "filename": template_filename}}
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to save template",
                exc_info=True,
                extra={"extra_data": {"vendor": vendor_name, "error": str(e)}}
            )
            return False

    def _get_template_filename(self, vendor_name: str) -> str:
        """
        Generate sanitized template filename from vendor name.

        Args:
            vendor_name: Name of the vendor

        Returns:
            Sanitized filename (e.g., "com.vendor_name.yml")
        """
        # Create sanitized filename from vendor name
        vendor_slug = vendor_name.lower().replace(" ", "_").replace(",", "").replace(".", "")
        vendor_slug = re.sub(r'[^a-z0-9_]', '', vendor_slug)
        return f"com.{vendor_slug}.yml"
