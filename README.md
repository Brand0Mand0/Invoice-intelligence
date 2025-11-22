# Invoice Intelligence 🧾

AI-powered invoice processing system with automated data extraction, analysis, and insights using NEAR AI.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0-FF4B4B.svg)](https://streamlit.io)

## Features

### 🔒 Security (Production-Ready)
- **File Upload Security** - 5-layer validation with magic byte verification, path traversal protection, and DoS prevention
- **CORS Protection** - Environment-based origin whitelisting
- **Data Sanitization** - Comprehensive log sanitization preventing API key/PII leaks
- **Input Validation** - Strict validation on all user inputs

### 🤖 AI-Powered Extraction
- **NEAR AI Integration** - Using DeepSeek-V3.1 for intelligent invoice parsing
- **Automatic Field Extraction** - Vendor, date, amount, invoice number, category
- **Vendor Normalization** - Smart vendor name matching and deduplication
- **High Accuracy** - 95%+ confidence scores on standard invoices

### 📊 Analytics & Insights
- **Spending Analysis** - Track spending by vendor, category, and time period
- **Recurring Detection** - Automatically identifies recurring expenses
- **Export Capabilities** - CSV export for accounting software
- **Interactive Dashboard** - Streamlit-based UI for easy management

---

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 14+
- NEAR AI API key ([Get one here](https://cloud.near.ai))

### Installation

\`\`\`bash
# Clone repository
git clone https://github.com/yourusername/invoice_intelligence.git
cd invoice_intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
\`\`\`

### Database Setup

\`\`\`bash
createdb invoice_db
python -c "from app.core.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"
\`\`\`

### Run Application

\`\`\`bash
# Terminal 1: Start backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start dashboard
streamlit run dashboard/app.py --server.port 8501
\`\`\`

Access: Dashboard at http://localhost:8501 | API at http://localhost:8000/docs

---

## Roadmap

See [SPEC.md](SPEC.md) for detailed technical specification.

**Next Steps:**
- [ ] Rate Limiting
- [ ] Authentication
- [ ] Health Checks
- [ ] Connection Pooling

---

## Tech Stack

FastAPI | Streamlit | PostgreSQL | NEAR AI | SQLAlchemy | pdfplumber

---

Built with ❤️ for automated invoice processing
