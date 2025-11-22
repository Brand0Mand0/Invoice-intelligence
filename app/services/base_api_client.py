"""
Base API client for making HTTP requests to external services.

Provides common functionality for HTTP client operations including:
- Authenticated requests
- Error handling
- Timeout configuration
- JSON response parsing
"""

import httpx
from typing import Dict, Any, Optional
from app.utils.sanitizer import sanitize_response_text
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class BaseAPIClient:
    """Base class for API clients with common HTTP functionality."""

    def __init__(self, base_url: str, api_key: str, timeout: float):
        """
        Initialize base API client.

        Args:
            base_url: Base URL for API endpoints
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Build request headers with authentication.

        Args:
            additional_headers: Optional additional headers to include

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if additional_headers:
            headers.update(additional_headers)

        return headers

    async def _post(
        self,
        endpoint: str,
        json_data: Dict[str, Any],
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated POST request to API endpoint.

        Args:
            endpoint: API endpoint path (e.g., "/v1/chat/completions")
            json_data: JSON payload for request body
            additional_headers: Optional additional headers

        Returns:
            Parsed JSON response

        Raises:
            Exception: If request fails or returns non-200 status
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(additional_headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=headers,
                json=json_data
            )

            if response.status_code != 200:
                # Sanitize response to prevent leaking sensitive data in logs
                safe_response = sanitize_response_text(response.text)
                logger.error(
                    "API POST request failed",
                    extra={
                        "extra_data": {
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "response": safe_response
                        }
                    }
                )
                raise Exception(f"API request failed with status {response.status_code}")

            return response.json()

    async def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated GET request to API endpoint.

        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            additional_headers: Optional additional headers

        Returns:
            Parsed JSON response

        Raises:
            Exception: If request fails or returns non-200 status
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(additional_headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                headers=headers,
                params=params
            )

            if response.status_code != 200:
                # Sanitize response to prevent leaking sensitive data in logs
                safe_response = sanitize_response_text(response.text)
                logger.error(
                    "API GET request failed",
                    extra={
                        "extra_data": {
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "response": safe_response
                        }
                    }
                )
                raise Exception(f"API request failed with status {response.status_code}")

            return response.json()
