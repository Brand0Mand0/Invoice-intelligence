import httpx
from typing import Dict, Any, Optional

# Dashboard configuration (independent from backend)
FASTAPI_PORT = 8000
API_BASE_URL = f"http://localhost:{FASTAPI_PORT}/api"


async def upload_pdf(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Upload PDF to API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"file": (filename, file_bytes, "application/pdf")}
        response = await client.post(f"{API_BASE_URL}/upload", files=files)
        response.raise_for_status()
        return response.json()


async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get processing job status."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/status/{job_id}")
        response.raise_for_status()
        return response.json()


async def get_invoices() -> Dict[str, Any]:
    """Get all invoices."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/invoices")
        response.raise_for_status()
        return response.json()


async def get_vendors() -> Dict[str, Any]:
    """Get all vendors."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/vendors")
        response.raise_for_status()
        return response.json()


async def get_monthly_analytics() -> Dict[str, Any]:
    """Get monthly analytics."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/analytics/monthly")
        response.raise_for_status()
        return response.json()


async def get_top_vendors(limit: int = 10) -> Dict[str, Any]:
    """Get top vendors."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/analytics/top-vendors?limit={limit}")
        response.raise_for_status()
        return response.json()


async def get_summary() -> Dict[str, Any]:
    """Get summary statistics."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/analytics/summary")
        response.raise_for_status()
        return response.json()


async def send_chat_query(query: str) -> Dict[str, Any]:
    """Send chat query to API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/chat",
            json={"query": query}
        )
        response.raise_for_status()
        return response.json()


async def get_chat_history(limit: int = 50) -> Dict[str, Any]:
    """Get chat history."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_BASE_URL}/chat/history?limit={limit}")
        response.raise_for_status()
        return response.json()


def export_csv_url() -> str:
    """Get export CSV URL."""
    return f"{API_BASE_URL}/export/csv"
