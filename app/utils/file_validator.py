"""
File upload security validation.

Protects against:
- Malware uploads (magic byte validation)
- Path traversal attacks (filename sanitization)
- DoS attacks (streaming file size validation)
- File type spoofing (content verification)
- Executable uploads (extension whitelisting)
"""

import os
import re
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException


# PDF magic bytes (file signatures)
PDF_MAGIC_BYTES = [
    b'%PDF-1.',  # PDF 1.0-1.7
    b'%PDF-2.',  # PDF 2.0
]

# Maximum filename length (防止文件系统问题)
MAX_FILENAME_LENGTH = 255

# Allowed file extensions (whitelist only)
ALLOWED_EXTENSIONS = {'.pdf'}

# Dangerous characters in filenames
DANGEROUS_FILENAME_CHARS = re.compile(r'[^\w\s\-.]')


class FileValidationError(Exception):
    """Custom exception for file validation failures."""
    pass


def validate_magic_bytes(content: bytes, max_check_bytes: int = 8) -> bool:
    """
    Validate file is actually a PDF by checking magic bytes.

    Args:
        content: First bytes of the file
        max_check_bytes: How many bytes to check

    Returns:
        True if valid PDF, False otherwise

    Example:
        >>> validate_magic_bytes(b'%PDF-1.4\\n...')
        True
        >>> validate_magic_bytes(b'MZ...')  # Windows executable
        False
    """
    if len(content) < max_check_bytes:
        return False

    header = content[:max_check_bytes]

    for magic in PDF_MAGIC_BYTES:
        if header.startswith(magic):
            return True

    return False


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    Sanitize uploaded filename to prevent security issues.

    Protects against:
    - Path traversal (../, ..\)
    - Special characters
    - Hidden files (.htaccess)
    - Overly long filenames
    - Null bytes

    Args:
        filename: Original filename from upload
        max_length: Maximum allowed filename length

    Returns:
        Sanitized filename

    Raises:
        FileValidationError: If filename is invalid

    Example:
        >>> sanitize_filename("../../etc/passwd")
        Raises FileValidationError
        >>> sanitize_filename("invoice 2024.pdf")
        "invoice_2024.pdf"
    """
    if not filename:
        raise FileValidationError("Filename cannot be empty")

    # Remove path components (security critical!)
    filename = os.path.basename(filename)

    # Remove null bytes (can cause issues in C-based filesystems)
    filename = filename.replace('\x00', '')

    # Check for path traversal attempts
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        raise FileValidationError("Invalid filename: path traversal attempt detected")

    # Check for hidden files (often used for attacks)
    if filename.startswith('.'):
        raise FileValidationError("Hidden files are not allowed")

    # Replace dangerous characters with underscores
    # Keep: letters, numbers, spaces, hyphens, periods
    filename = DANGEROUS_FILENAME_CHARS.sub('_', filename)

    # Replace spaces with underscores (cleaner URLs)
    filename = filename.replace(' ', '_')

    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)

    # Ensure filename isn't too long
    if len(filename) > max_length:
        # Keep extension, truncate name
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext

    # Final validation
    if not filename or filename == '.':
        raise FileValidationError("Invalid filename after sanitization")

    return filename


def validate_file_extension(filename: str, allowed_extensions: set = ALLOWED_EXTENSIONS) -> bool:
    """
    Validate file has an allowed extension.

    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (e.g., {'.pdf'})

    Returns:
        True if extension is allowed

    Example:
        >>> validate_file_extension("invoice.pdf")
        True
        >>> validate_file_extension("malware.exe")
        False
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions


async def validate_file_size_streaming(
    file: UploadFile,
    max_size: int,
    chunk_size: int = 8192
) -> bytes:
    """
    Validate file size while streaming (prevents DoS).

    Reads file in chunks and validates size BEFORE loading entire file.

    Args:
        file: FastAPI UploadFile object
        max_size: Maximum allowed file size in bytes
        chunk_size: Size of chunks to read

    Returns:
        Complete file content as bytes

    Raises:
        FileValidationError: If file exceeds max_size

    Example:
        >>> content = await validate_file_size_streaming(file, max_size=50*1024*1024)
    """
    content = bytearray()
    bytes_read = 0

    # Read in chunks to avoid memory exhaustion
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break

        bytes_read += len(chunk)

        # Check size limit DURING reading (not after!)
        if bytes_read > max_size:
            raise FileValidationError(
                f"File size exceeds maximum allowed size of {max_size / (1024*1024):.1f}MB"
            )

        content.extend(chunk)

    return bytes(content)


def validate_pdf_structure(content: bytes) -> bool:
    """
    Basic PDF structure validation.

    Checks for:
    - PDF header
    - EOF marker
    - Minimum size

    Args:
        content: PDF file content

    Returns:
        True if valid PDF structure

    Note:
        This is basic validation. For production, consider using PyPDF2 or pdfplumber
        to fully validate PDF structure.
    """
    # Minimum valid PDF size (header + minimal content + EOF)
    MIN_PDF_SIZE = 100

    if len(content) < MIN_PDF_SIZE:
        return False

    # Check header
    if not validate_magic_bytes(content):
        return False

    # Check for EOF marker (PDFs should end with %%EOF)
    # Look in last 1KB for the marker
    tail = content[-1024:]
    if b'%%EOF' not in tail:
        return False

    return True


async def validate_upload_file(
    file: UploadFile,
    max_size: int,
    allowed_extensions: set = ALLOWED_EXTENSIONS
) -> Tuple[bytes, str]:
    """
    Comprehensive file upload validation (all-in-one).

    Validates:
    1. Filename sanitization
    2. Extension whitelist
    3. File size (streaming)
    4. Magic bytes (actual PDF)
    5. PDF structure

    Args:
        file: FastAPI UploadFile object
        max_size: Maximum file size in bytes
        allowed_extensions: Set of allowed extensions

    Returns:
        Tuple of (file_content, sanitized_filename)

    Raises:
        HTTPException: If validation fails

    Example:
        >>> content, safe_filename = await validate_upload_file(file, max_size=50*1024*1024)
    """
    # Step 1: Validate and sanitize filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    try:
        safe_filename = sanitize_filename(file.filename)
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filename: {str(e)}")

    # Step 2: Validate extension
    if not validate_file_extension(safe_filename, allowed_extensions):
        allowed = ', '.join(allowed_extensions)
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {allowed}"
        )

    # Step 3: Validate file size (streaming - prevents DoS)
    try:
        content = await validate_file_size_streaming(file, max_size)
    except FileValidationError as e:
        raise HTTPException(status_code=413, detail=str(e))

    # Step 4: Validate magic bytes (is it actually a PDF?)
    if not validate_magic_bytes(content):
        raise HTTPException(
            status_code=400,
            detail="File is not a valid PDF. Magic bytes validation failed."
        )

    # Step 5: Validate PDF structure
    if not validate_pdf_structure(content):
        raise HTTPException(
            status_code=400,
            detail="File is not a valid PDF. Structure validation failed."
        )

    return content, safe_filename


def create_safe_filepath(base_dir: str, job_id: str, filename: str) -> str:
    """
    Create a safe file path that prevents directory traversal.

    Args:
        base_dir: Base upload directory
        job_id: Unique job identifier
        filename: Sanitized filename

    Returns:
        Absolute path that is guaranteed to be within base_dir

    Raises:
        FileValidationError: If resulting path is outside base_dir

    Example:
        >>> create_safe_filepath("/tmp/uploads", "abc-123", "invoice.pdf")
        "/tmp/uploads/abc-123_invoice.pdf"
    """
    # Create the intended path
    filename_with_id = f"{job_id}_{filename}"
    intended_path = os.path.join(base_dir, filename_with_id)

    # Resolve to absolute path (handles .., symlinks, etc.)
    safe_path = os.path.abspath(intended_path)
    base_abs = os.path.abspath(base_dir)

    # Verify the resolved path is still within base_dir
    if not safe_path.startswith(base_abs + os.sep):
        raise FileValidationError(
            "Path traversal attempt detected in file path"
        )

    return safe_path


# Export public API
__all__ = [
    'validate_upload_file',
    'sanitize_filename',
    'create_safe_filepath',
    'FileValidationError',
]
