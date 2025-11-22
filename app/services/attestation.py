import httpx
from typing import Dict, Optional
from app.core.config import get_settings
from app.core.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TEEVerifier:
    """Service for verifying TEE (Trusted Execution Environment) attestations from NEAR AI Cloud."""

    def __init__(self):
        self.base_url = settings.NEAR_AI_BASE_URL
        self.api_key = settings.NEAR_AI_API_KEY
        self.timeout = 10.0

    async def get_signature(self, completion_id: str, model: str = "zai-org/GLM-4.6") -> Optional[Dict]:
        """
        Fetch the cryptographic signature for a chat completion.

        According to NEAR AI docs, signatures are stored in memory for 5 minutes.
        Endpoint: GET /v1/signature/{chat_id}?model={model}&signing_algo=ecdsa

        Args:
            completion_id: The chat completion ID from NEAR AI response
            model: The model used for inference

        Returns:
            Signature data containing:
            - text: Concatenated request and response hashes (format: request_hash:response_hash)
            - signature: ECDSA signature of the text field
            - signing_address: Public key matching the attestation
            - signing_algo: Cryptography algorithm used (ecdsa)
        """
        if not completion_id:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v1/signature/{completion_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    params={
                        "model": model,
                        "signing_algo": "ecdsa"
                    }
                )

                if response.status_code != 200:
                    logger.warning(
                        "Failed to fetch TEE signature",
                        extra={
                            "extra_data": {
                                "completion_id": completion_id,
                                "status_code": response.status_code,
                                "response": response.text
                            }
                        }
                    )
                    return None

                return response.json()

        except Exception as e:
            logger.error(
                "TEE signature fetch error",
                exc_info=True,
                extra={"extra_data": {"completion_id": completion_id, "error": str(e)}}
            )
            return None

    async def get_attestation_report(self, model: str = "zai-org/GLM-4.6") -> Optional[Dict]:
        """
        Get the TEE attestation report for a specific model.
        Endpoint: GET /v1/attestation/report?model={model}

        Returns attestation report containing:
        - signing_address: Public key generated inside the TEE
        - nvidia_payload: Attestation report for NVIDIA TEE verification
        - intel_quote: Attestation report for Intel TDX verification
        - all_attestations: Array of attestations from all GPU nodes

        Args:
            model: The model to get attestation report for

        Returns:
            Attestation report or None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/v1/attestation/report",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    params={"model": model}
                )

                if response.status_code != 200:
                    logger.warning(
                        "Failed to fetch TEE attestation report",
                        extra={
                            "extra_data": {
                                "model": model,
                                "status_code": response.status_code,
                                "response": response.text
                            }
                        }
                    )
                    return None

                return response.json()

        except Exception as e:
            logger.error(
                "TEE attestation report fetch error",
                exc_info=True,
                extra={"extra_data": {"model": model, "error": str(e)}}
            )
            return None

    def format_completion_id(self, completion_id: Optional[str]) -> str:
        """
        Format completion ID for display.

        Args:
            completion_id: The chat completion ID

        Returns:
            Formatted display string
        """
        if completion_id:
            # Show first 8 and last 8 characters for readability
            if len(completion_id) > 20:
                return f"{completion_id[:12]}...{completion_id[-8:]}"
            return completion_id
        return "Not available"
