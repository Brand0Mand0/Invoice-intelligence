# Invoice Intelligence - Technical Specification

## Project Overview

AI-powered invoice processing system with NEAR AI integration for automated invoice data extraction, analysis, and insights.

**Stack:**
- Backend: FastAPI (Python)
- Frontend: Streamlit
- Database: PostgreSQL
- AI: NEAR AI (DeepSeek-V3.1)
- PDF Processing: pdfplumber, invoice2data

---

## Completed Features ✅

### Security
- ✅ **Data Sanitization** - Comprehensive log sanitization preventing API key/PII leaks
- ✅ **CORS Security** - Environment-based origin whitelisting
- ✅ **File Upload Security** - 5-layer validation (magic bytes, path traversal, DoS protection, PDF structure)
- ✅ **Structured Logging** - JSON logging with security audit trails

### Core Features
- ✅ **PDF Upload** - Secure file upload with comprehensive validation
- ✅ **AI Extraction** - NEAR AI integration for invoice data extraction
- ✅ **Background Processing** - Async job queue for PDF processing
- ✅ **Database Models** - Invoice, ProcessingJob, vendor normalization
- ✅ **Streamlit Dashboard** - Upload interface and invoice viewer

---

## High-Priority Roadmap 🚀

### 1. Rate Limiting (2 hours)
**Priority:** Critical
**Estimated Effort:** 2 hours

Prevent DoS attacks and cost exploitation from unlimited NEAR AI calls.

**Implementation:**
- Redis-based rate limiting using `slowapi`
- Endpoint limits:
  - `/api/upload`: 10 requests/minute per IP
  - `/api/chat`: 5 requests/minute per IP
  - Global: 100 requests/minute per IP
- Cost protection: Track NEAR AI token usage per user

**Dependencies:**
- Redis server
- `slowapi` package
- `redis-py` package

**Files to modify:**
- `app/main.py` - Add rate limiting middleware
- `app/core/config.py` - Redis configuration
- `requirements.txt` - Add dependencies

---

### 2. Authentication (2-3 hours)
**Priority:** Critical
**Estimated Effort:** 2-3 hours

Protect API endpoints from unauthorized access.

**Implementation Options:**

**Option A: API Key (Simpler)**
- Generate API keys for users
- Store hashed keys in database
- Validate via `X-API-Key` header
- Per-user rate limits

**Option B: OAuth2 (Production-ready)**
- OAuth2 with JWT tokens
- Token expiration and refresh
- User roles (admin, user)
- Integration with social providers (Google, GitHub)

**Recommendation:** Start with API key, migrate to OAuth2 later

**Files to create:**
- `app/models/api_key.py` - API key model
- `app/api/deps.py` - Auth dependencies
- `app/services/auth.py` - Auth service

**Files to modify:**
- All API routes - Add `Depends(verify_api_key)`
- `app/core/config.py` - Auth settings

---

### 3. Health Checks (30 minutes)
**Priority:** High
**Estimated Effort:** 30 minutes

Proper service health monitoring for production deployment.

**Implementation:**
- Database connection check
- NEAR AI API availability check
- Disk space check (upload directory)
- Response time metrics

**Endpoints:**
- `/health` - Overall health status
- `/health/database` - Database status
- `/health/ai` - NEAR AI status
- `/health/storage` - Storage status

**Files to modify:**
- `app/main.py` - Expand health check endpoint
- `app/services/health.py` - Health check service (new)

---

### 4. Database Connection Pooling (30 minutes)
**Priority:** High
**Estimated Effort:** 30 minutes

Optimize database performance and prevent connection exhaustion.

**Implementation:**
- Configure SQLAlchemy pool settings
- Pool size: 20 connections
- Pool overflow: 10 connections
- Pool timeout: 30 seconds
- Connection recycling: 1 hour

**Files to modify:**
- `app/core/database.py` - Add pool configuration

---

## Code Quality Improvements 📝

### 5. Type Hints (3-4 hours)
**Priority:** Medium
**Estimated Effort:** 3-4 hours

Improve code maintainability and catch errors early.

**Implementation:**
- Add type hints to all functions
- Add return type annotations
- Add parameter type annotations
- Run `mypy` for type checking

**Files to update:**
- All Python files in `app/`
- Focus on: services, models, routes

---

### 6. Configuration Cleanup (1 hour)
**Priority:** Medium
**Estimated Effort:** 1 hour

Move hardcoded values to configuration.

**Current Issues:**
- Magic numbers scattered throughout code
- Hardcoded file paths
- Hardcoded error messages

**Implementation:**
- Create `app/core/constants.py` for all constants
- Move magic numbers to named constants
- Move error messages to centralized location

---

### 7. Observability (3-4 hours)
**Priority:** Low (Future)
**Estimated Effort:** 3-4 hours

Production-grade observability with OpenTelemetry.

**Implementation:**
- OpenTelemetry instrumentation
- Distributed tracing
- Metrics collection (request count, latency, errors)
- Integration with observability platforms (Datadog, New Relic, etc.)

**Dependencies:**
- `opentelemetry-api`
- `opentelemetry-sdk`
- `opentelemetry-instrumentation-fastapi`
- `opentelemetry-exporter-otlp`

---

## Future Features 🔮

### Analytics Enhancements
- Spending trends visualization
- Vendor spend analysis
- Recurring expense detection
- Budget alerts

### AI Improvements
- Multi-invoice batch processing
- Invoice categorization improvement
- Anomaly detection (unusual amounts)
- Receipt vs. invoice distinction

### Integration
- Accounting software integration (QuickBooks, Xero)
- Email invoice forwarding (Gmail, Outlook)
- Cloud storage integration (Dropbox, Google Drive)

### Export Features
- CSV export enhancements
- Excel export with formatting
- PDF report generation
- Automated monthly reports

---

## Technical Debt

### Current Issues
- `invoice2data` library errors (minor, using NEAR AI as primary)
- Verbose SQLAlchemy logging in development
- No automated tests
- No CI/CD pipeline

### Testing Strategy (Future)
- Unit tests with pytest
- Integration tests for API endpoints
- End-to-end tests for upload flow
- Load testing for rate limits

### DevOps (Future)
- Docker containerization
- Docker Compose for local development
- CI/CD with GitHub Actions
- Automated deployment (Render, Railway, Fly.io)

---

## Security Improvements (Completed)

| Feature | Status | Priority | Completed |
|---------|--------|----------|-----------|
| Data Sanitization | ✅ Complete | Critical | 2025-11 |
| CORS Security | ✅ Complete | Critical | 2025-11 |
| File Upload Security | ✅ Complete | Critical | 2025-11 |
| Rate Limiting | ⏳ Planned | Critical | - |
| Authentication | ⏳ Planned | Critical | - |
| Input Validation | ✅ Complete | High | 2025-11 |
| SQL Injection Protection | ✅ Complete | High | 2025-11 (SQLAlchemy ORM) |

---

## Deployment Readiness Checklist

### Before Production Deploy:
- [ ] Rate limiting implemented
- [ ] Authentication implemented
- [ ] Environment variables secured (secrets management)
- [ ] Database connection pooling configured
- [ ] Health checks implemented
- [ ] Error monitoring setup (Sentry)
- [ ] Backup strategy for database
- [ ] Backup strategy for uploaded files
- [ ] SSL/TLS certificates configured
- [ ] Domain configured
- [ ] Load testing completed
- [ ] Security audit completed

---

## Development Setup

```bash
# Clone repository
git clone <repo-url>
cd invoice_intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Setup database
# (PostgreSQL must be running)
python -c "from app.core.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"

# Run backend
uvicorn app.main:app --reload --port 8000

# Run frontend (separate terminal)
streamlit run dashboard/app.py --server.port 8501
```

---

## Contributing

### Code Standards
- Follow PEP 8 style guide
- Add type hints to all functions
- Write docstrings for public functions
- Add logging for important operations
- Never commit secrets or API keys

### Security Guidelines
- All user input must be validated
- All file uploads must pass security checks
- All API responses must be sanitized
- All database queries must use ORM (no raw SQL)
- All errors must be logged with sanitized data

---

## License

[Add your license here]

## Contact

[Add contact information here]
