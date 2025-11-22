"""
Comprehensive tests for TemplateManager.

Tests template loading, saving, and filename generation.
"""

import pytest
import os
from unittest.mock import Mock, patch, mock_open

from app.services.template_manager import TemplateManager


class TestTemplateManager:
    """Test suite for TemplateManager class."""

    @pytest.fixture
    def temp_template_dir(self, tmp_path):
        """Create temporary template directory."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        return str(template_dir)

    @pytest.fixture
    def template_manager(self, temp_template_dir):
        """Create TemplateManager with temporary directory."""
        return TemplateManager(template_dir=temp_template_dir)

    def test_init_default_directory(self):
        """Test TemplateManager initialization with default directory."""
        with patch('os.path.abspath') as mock_abspath:
            mock_abspath.return_value = "/app/services/template_manager.py"
            manager = TemplateManager()
            # Should create path relative to services directory
            assert "templates" in manager.template_dir

    def test_init_custom_directory(self, temp_template_dir):
        """Test TemplateManager initialization with custom directory."""
        manager = TemplateManager(template_dir=temp_template_dir)
        assert manager.template_dir == temp_template_dir

    def test_load_templates_success(self, template_manager, temp_template_dir):
        """Test successful template loading."""
        # Create test template file
        template_file = os.path.join(temp_template_dir, "com.test_vendor.yml")
        with open(template_file, 'w') as f:
            f.write("issuer: Test Vendor\n")

        with patch('invoice2data.extract.loader.read_templates') as mock_read:
            mock_read.return_value = [Mock(), Mock()]  # 2 mock templates

            templates = template_manager.load_templates()

            mock_read.assert_called_once_with(temp_template_dir)
            assert len(templates) == 2

    def test_load_templates_directory_not_exists(self, template_manager):
        """Test template loading when directory doesn't exist."""
        # Use non-existent directory
        template_manager.template_dir = "/nonexistent/path"

        templates = template_manager.load_templates()

        assert templates == []

    def test_load_templates_error_handling(self, template_manager):
        """Test template loading handles errors gracefully."""
        with patch('invoice2data.extract.loader.read_templates') as mock_read:
            mock_read.side_effect = Exception("Read error")

            templates = template_manager.load_templates()

            assert templates == []

    def test_template_exists_true(self, template_manager, temp_template_dir):
        """Test template exists check returns True when file exists."""
        # Create template file
        template_file = os.path.join(temp_template_dir, "com.test_vendor.yml")
        with open(template_file, 'w') as f:
            f.write("issuer: Test Vendor\n")

        assert template_manager.template_exists("Test Vendor") is True

    def test_template_exists_false(self, template_manager):
        """Test template exists check returns False when file doesn't exist."""
        assert template_manager.template_exists("Nonexistent Vendor") is False

    def test_template_exists_invalid_vendor_name(self, template_manager):
        """Test template exists returns False for invalid vendor names."""
        assert template_manager.template_exists("") is False
        assert template_manager.template_exists("Unknown Vendor") is False
        assert template_manager.template_exists(None) is False

    def test_save_template_success(self, template_manager, temp_template_dir):
        """Test successful template saving."""
        vendor_name = "Test Company"
        yaml_content = """issuer: Test Company
invoice_number: pattern
amount: pattern"""

        result = template_manager.save_template(vendor_name, yaml_content)

        assert result is True

        # Verify file was created
        expected_file = os.path.join(temp_template_dir, "com.test_company.yml")
        assert os.path.exists(expected_file)

        # Verify content
        with open(expected_file, 'r') as f:
            content = f.read()
            assert "Test Company" in content

    def test_save_template_invalid_vendor_name(self, template_manager):
        """Test save template fails with invalid vendor name."""
        result = template_manager.save_template("", "yaml content")
        assert result is False

        result = template_manager.save_template("Unknown Vendor", "yaml content")
        assert result is False

    def test_save_template_creates_directory(self, tmp_path):
        """Test save template creates directory if it doesn't exist."""
        nonexistent_dir = str(tmp_path / "new_templates")
        manager = TemplateManager(template_dir=nonexistent_dir)

        vendor_name = "Test Vendor"
        yaml_content = "issuer: Test Vendor"

        result = manager.save_template(vendor_name, yaml_content)

        assert result is True
        assert os.path.exists(nonexistent_dir)

    def test_save_template_error_handling(self, template_manager):
        """Test save template handles errors gracefully."""
        # Use invalid directory to trigger error
        template_manager.template_dir = "/invalid/path/that/cannot/be/created"

        result = template_manager.save_template("Test Vendor", "yaml content")

        assert result is False

    def test_get_template_filename_basic(self, template_manager):
        """Test template filename generation."""
        filename = template_manager._get_template_filename("Test Vendor")
        assert filename == "com.test_vendor.yml"

    def test_get_template_filename_with_spaces(self, template_manager):
        """Test template filename generation with spaces."""
        filename = template_manager._get_template_filename("Test  Vendor  Name")
        # Multiple spaces become double underscores, single spaces become single underscores
        assert filename == "com.test__vendor__name.yml"

    def test_get_template_filename_with_special_chars(self, template_manager):
        """Test template filename generation with special characters."""
        filename = template_manager._get_template_filename("Test, Inc. & Co.")
        assert filename == "com.test_inc__co.yml"
        assert "," not in filename
        # Check that dots are removed from vendor name (but "com." prefix remains)
        assert filename.startswith("com.")
        vendor_part = filename.replace("com.", "").replace(".yml", "")
        assert "." not in vendor_part
        assert "&" not in filename

    def test_get_template_filename_with_numbers(self, template_manager):
        """Test template filename generation preserves numbers."""
        filename = template_manager._get_template_filename("Company 123")
        assert filename == "com.company_123.yml"

    def test_get_template_filename_all_lowercase(self, template_manager):
        """Test template filename is all lowercase."""
        filename = template_manager._get_template_filename("TEST VENDOR")
        assert filename == "com.test_vendor.yml"
        assert filename.islower() or filename.endswith(".yml")

    def test_get_template_filename_unicode_chars(self, template_manager):
        """Test template filename strips unicode characters."""
        filename = template_manager._get_template_filename("Test Café")
        # Unicode chars should be removed
        assert "é" not in filename
        assert filename.startswith("com.")
        assert filename.endswith(".yml")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
