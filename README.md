# Invoice Intelligence 🧾

AI-powered invoice processing system with semantic search, automated data extraction, and intelligent analytics.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0-FF4B4B.svg)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

### 🤖 AI-Powered Intelligence

- **NEAR AI Integration** - DeepSeek-V3.1 for intelligent invoice parsing with 95%+ accuracy
- **Semantic Search** - Natural language queries using BGE-Large embeddings (100% local & private)
- **Vector Similarity** - Find similar invoices using pgvector cosine distance
- **Smart Vendor Normalization** - Automatic vendor name matching and deduplication
- **Conversational AI** - Ask questions about your invoices in natural language
- **Automatic Field Extraction** - Vendor, date, amount, invoice number, category, line items

### 📊 Analytics & Insights

- **Spending Analysis** - Track spending by vendor, category, and time period
- **Recurring Detection** - Automatically identifies recurring expenses
- **Similar Invoice Discovery** - Find related expenses based on semantic similarity
- **Interactive Dashboard** - Streamlit-based UI with real-time visualizations
- **Export Capabilities** - CSV export for accounting software integration
- **Monthly Trends** - Visualize spending patterns over time

### 🔒 Security & Privacy

- **100% Private Embeddings** - BGE model runs entirely on your infrastructure
- **File Upload Security** - 5-layer validation with magic byte verification, path traversal protection, and DoS prevention
- **CORS Protection** - Environment-based origin whitelisting
- **Data Sanitization** - Comprehensive log sanitization preventing API key/PII leaks
- **Input Validation** - Strict validation on all user inputs

---

## Architecture

### System Architecture

```mermaid
flowchart TB
    subgraph "Frontend"
        UI[Streamlit Dashboard<br/>:8501]
    end

    subgraph "Backend"
        API[FastAPI<br/>:8000]
        PARSER[PDF Parser]
        EMBED[BGE Embeddings<br/>Local/Private]
    end

    subgraph "AI Services"
        NEAR[NEAR AI Cloud<br/>DeepSeek V3.1]
    end

    subgraph "Database"
        PG[(PostgreSQL 17<br/>+ pgvector)]
    end

    UI <--> API
    API --> PARSER
    PARSER --> NEAR
    PARSER --> EMBED
    EMBED --> PG
    API <--> PG

    style UI fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style API fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style NEAR fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    style PG fill:#fce4ec,stroke:#880e4f,stroke-width:2px
```

### Data Processing Flow

```mermaid
flowchart LR
    PDF[PDF Invoice] --> UPLOAD[Upload]
    UPLOAD --> EXTRACT{Extract Data}

    EXTRACT -->|Primary| I2D[invoice2data]
    EXTRACT -->|Fallback| AI[NEAR AI<br/>DeepSeek]

    I2D --> NORM[Normalize<br/>Vendors]
    AI --> NORM

    NORM --> EMBED[Generate<br/>Embeddings]
    EMBED --> STORE[(Store in<br/>PostgreSQL)]

    STORE --> SEARCH[Semantic<br/>Search]
    STORE --> ANALYTICS[Analytics<br/>Dashboard]
    STORE --> CHAT[AI Chat<br/>Interface]

    style PDF fill:#ffd54f,stroke:#f57c00,stroke-width:2px
    style STORE fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px
    style SEARCH fill:#c5e1a5,stroke:#558b2f,stroke-width:2px
    style ANALYTICS fill:#c5e1a5,stroke:#558b2f,stroke-width:2px
    style CHAT fill:#c5e1a5,stroke:#558b2f,stroke-width:2px
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 17+ with pgvector extension
- NEAR AI API key ([Get one here](https://cloud.near.ai))

### Installation

```bash
# Clone repository
git clone https://github.com/Brand0Mand0/Invoice-intelligence.git
cd invoice_intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the project root:

```bash
# Required
NEAR_AI_API_KEY=your_near_ai_key_here
DATABASE_URL=postgresql://user:pass@localhost/invoice_db

# Optional (with defaults)
EMBEDDING_PROVIDER=bge              # "bge" (local) or "openai" (API)
ENVIRONMENT=development             # "development" or "production"
STREAMLIT_PORT=8501
FASTAPI_PORT=8000
```

### Database Setup

```bash
# Create database
createdb invoice_db

# Enable pgvector extension
psql invoice_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
alembic upgrade head
```

### Run Application

```bash
# Terminal 1: Start backend API
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start dashboard
source venv/bin/activate
streamlit run dashboard/app.py --server.port 8501
```

**Access Points:**
- Dashboard: http://localhost:8501
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## API Endpoints

### Invoice Management
- `POST /api/upload` - Upload and process invoice PDF
- `GET /api/invoices` - List all invoices (paginated)
- `GET /api/invoices/{id}` - Get invoice details
- `DELETE /api/invoices/{id}` - Delete invoice

### Semantic Search
- `GET /api/search/semantic?query={text}` - Natural language search
- `GET /api/invoices/{id}/similar?limit=5` - Find similar invoices

### Analytics
- `GET /api/analytics/summary` - Spending summary
- `GET /api/analytics/monthly` - Monthly trends
- `GET /api/analytics/top-vendors` - Vendor rankings
- `GET /api/analytics/category-breakdown` - Spending by category

### Chat & Insights
- `POST /api/chat` - AI-powered invoice Q&A

### System
- `GET /health` - Health check

---

## Tech Stack

### Backend
- **FastAPI 0.104.1** - Modern REST API framework
- **Uvicorn 0.24.0** - ASGI server
- **SQLAlchemy 2.0.23** - ORM and database toolkit
- **Alembic 1.12.1** - Database migrations

### Frontend
- **Streamlit 1.29.0** - Interactive dashboard
- **Plotly** - Data visualizations

### Database
- **PostgreSQL 17** - Primary database
- **pgvector 0.8.1** - Vector similarity search

### AI/ML
- **NEAR AI** - DeepSeek-V3.1 for invoice parsing
- **BGE-Large** - Local embeddings (BAAI/bge-large-en-v1.5, 1024-dim)
- **sentence-transformers 5.1.2** - Embedding framework
- **invoice2data 0.4.4** - Template-based extraction

### PDF Processing
- **pdfplumber 0.10.3** - PDF text extraction
- **PyPDF2 3.0.1** - PDF utilities

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_embeddings.py
```

---

## Roadmap

### Planned Features

- [ ] **Redis Integration** - Caching layer for improved performance
- [ ] **Docker Deployment** - Containerized deployment with docker-compose
- [ ] **Google API Integration** - Automated email ingestion from Gmail
- [ ] **Neo4J Integration** - Graph RAG database for advanced relationship analysis
- [ ] **Rate Limiting** - API rate limiting and throttling
- [ ] **Authentication** - User authentication and authorization
- [ ] **Webhook Support** - Real-time notifications for processed invoices
- [ ] **Multi-language Support** - Invoice processing for non-English documents

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [NEAR AI](https://near.ai) for providing DeepSeek-V3.1 API access
- [BAAI](https://huggingface.co/BAAI) for the BGE-Large embedding model
- [pgvector](https://github.com/pgvector/pgvector) for vector similarity search in PostgreSQL

---

## Support

For issues, questions, or contributions, please open an issue on GitHub.

**Built with ❤️ for intelligent invoice processing**
