"""
Application-wide constants and configuration values.

This module centralizes all magic numbers, confidence scores, timeouts,
and other hardcoded values to improve maintainability.
"""

# ============================================================================
# VERSION INFORMATION
# ============================================================================

APP_VERSION = "1.0.0"
PARSER_VERSION = "1.0.0"


# ============================================================================
# CONFIDENCE SCORES
# ============================================================================

# Confidence score for template-based extraction (invoice2data)
CONFIDENCE_SCORE_TEMPLATE_MATCH = 0.95

# Confidence score for AI-based extraction (NEAR AI models)
CONFIDENCE_SCORE_AI_EXTRACTION = 0.95

# Confidence score for pdfplumber (deprecated but kept for reference)
CONFIDENCE_SCORE_PDFPLUMBER = 0.90


# ============================================================================
# API TIMEOUTS (in seconds)
# ============================================================================

# Timeout for NEAR AI API calls (extraction and template generation)
NEAR_AI_TIMEOUT_SECONDS = 30.0

# Timeout for NEAR AI attestation verification
ATTESTATION_TIMEOUT_SECONDS = 10.0

# Timeout for dashboard API calls to backend
DASHBOARD_API_TIMEOUT_SECONDS = 30.0

# Timeout for quick dashboard API calls (analytics, status checks)
DASHBOARD_API_TIMEOUT_SHORT_SECONDS = 10.0


# ============================================================================
# FILE UPLOAD & PROCESSING
# ============================================================================

# Maximum number of polling attempts when checking job status
# With 2-second sleep, this gives 120 seconds (2 minutes) total wait time
MAX_UPLOAD_POLLING_ATTEMPTS = 60

# Sleep duration between polling attempts (in seconds)
UPLOAD_POLLING_SLEEP_SECONDS = 2

# Progress bar weights for upload UI
UPLOAD_PROGRESS_UPLOAD_WEIGHT = 0.3  # 30% for file upload
UPLOAD_PROGRESS_PROCESSING_WEIGHT = 0.7  # 70% for processing


# ============================================================================
# AI MODEL CONFIGURATION
# ============================================================================

# Temperature for factual extraction (lower = more deterministic)
AI_TEMPERATURE_EXTRACTION = 0.1

# Temperature for template generation (lower = more consistent)
AI_TEMPERATURE_TEMPLATE_GENERATION = 0.1

# Temperature for chat/conversation (higher = more creative)
AI_TEMPERATURE_CHAT = 0.7

# Maximum tokens for AI responses
AI_MAX_TOKENS_EXTRACTION = 2000
AI_MAX_TOKENS_TEMPLATE = 1000
AI_MAX_TOKENS_CHAT = 1000


# ============================================================================
# INVOICE CATEGORIES
# ============================================================================

INVOICE_CATEGORIES = [
    "Software/SaaS",
    "Office Supplies",
    "Marketing/Advertising",
    "Professional Services",
    "Travel & Entertainment",
    "Utilities",
    "Equipment/Hardware",
    "Insurance",
    "Rent/Facilities",
    "Payroll Services",
    "Shipping/Fulfillment",
    "Other"
]

DEFAULT_CATEGORY = "Other"


# ============================================================================
# DATABASE CONSTRAINTS
# ============================================================================

# Maximum length for cache keys (pdf_hash + parser_version)
CACHE_KEY_MAX_LENGTH = 100

# Maximum length for vendor names
VENDOR_NAME_MAX_LENGTH = 255

# Maximum length for invoice numbers
INVOICE_NUMBER_MAX_LENGTH = 100

# Maximum length for category names
CATEGORY_MAX_LENGTH = 100

# Maximum length for purchaser names
PURCHASER_MAX_LENGTH = 100


# ============================================================================
# FILE PROCESSING
# ============================================================================

# Chunk size for computing file hashes (4KB)
FILE_HASH_CHUNK_SIZE = 4096

# Maximum text length to send to AI for template generation
TEMPLATE_GENERATION_MAX_TEXT_LENGTH = 2000


# ============================================================================
# DATE FORMATS
# ============================================================================

# Common date formats to try when parsing invoice dates
DATE_FORMATS = [
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%m/%d/%y",
    "%d/%m/%y"
]


# ============================================================================
# CHAT HISTORY
# ============================================================================

# Default number of chat conversations to load from history
DEFAULT_CHAT_HISTORY_LIMIT = 10


# ============================================================================
# ANALYTICS
# ============================================================================

# Default number of top vendors to show in analytics
DEFAULT_TOP_VENDORS_LIMIT = 10

# Maximum number of recent invoices to include in chat context
CHAT_CONTEXT_MAX_RECENT_INVOICES = 20

# Number of top vendors to include in chat context
CHAT_CONTEXT_TOP_VENDORS = 10
