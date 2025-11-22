import streamlit as st

st.set_page_config(
    page_title="Invoice Intelligence Platform",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page
st.title("📄 Invoice Intelligence Platform")
st.markdown("### AI-Powered Invoice Processing with NEAR AI")

st.markdown("""
Welcome to the Invoice Intelligence Platform. This system provides:

- **Automated PDF Processing**: Multi-tier extraction pipeline (pdfplumber → invoice2data → NEAR AI)
- **Vendor Normalization**: Automatic vendor name standardization
- **Analytics Dashboard**: Visualize spending trends and vendor metrics
- **AI Chat**: Natural language queries powered by NEAR AI GLM-4.6
- **TEE Attestation**: Trusted execution environment verification

---

### Getting Started

Use the sidebar to navigate:
- **Upload**: Upload and process invoice PDFs
- **Analytics**: View spending trends and insights
- **Chat**: Ask questions about your invoices
- **Data**: Browse and export invoice data

---

### System Status
""")

# Check API health
import asyncio
import httpx

# Dashboard configuration (independent from backend)
FASTAPI_PORT = 8000


async def check_api_health():
    """Check if API is running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://localhost:{FASTAPI_PORT}/health")
            if response.status_code == 200:
                return True, response.json()
            return False, None
    except Exception as e:
        return False, str(e)


try:
    health_ok, health_data = asyncio.run(check_api_health())

    if health_ok:
        st.success("✅ API is running and healthy")
        if health_data:
            st.json(health_data)
    else:
        st.error("❌ API is not responding. Please start the FastAPI server:")
        st.code(f"uvicorn app.main:app --reload --port {FASTAPI_PORT}")
except Exception as e:
    st.error(f"❌ Error checking API status: {e}")

st.markdown("---")
st.markdown("Powered by **NEAR AI** | Built with FastAPI & Streamlit")
