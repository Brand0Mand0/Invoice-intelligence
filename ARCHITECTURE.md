# Invoice Intelligence - System Architecture

## System Architecture Diagram

```mermaid
flowchart TB
    subgraph "User Interfaces"
        UI[Streamlit Dashboard<br/>:8501]
        API_DOCS[FastAPI Swagger<br/>:8000/docs]
    end

    subgraph "Application Layer"
        direction TB
        FASTAPI[FastAPI Backend<br/>:8000]

        subgraph "API Routes"
            UPLOAD[/api/upload]
            SEARCH[/api/search/semantic]
            SIMILAR[/api/invoices/{id}/similar]
            ANALYTICS[/api/analytics/*]
            CHAT[/api/chat]
        end
    end

    subgraph "Processing Services"
        direction LR
        PARSER[PDF Parser Service]
        EMBEDDINGS[Embedding Service]
        NEAR_AI[NEAR AI Service<br/>DeepSeek-V3.1]
        NORMALIZER[Vendor Normalizer]
    end

    subgraph "AI Models (Local)"
        BGE[BGE-Large<br/>1024-dim Embeddings<br/>100% Private]
        FALLBACK[OpenAI Embeddings<br/>Optional Fallback]
    end

    subgraph "Data Layer"
        direction TB
        POSTGRES[(PostgreSQL 17<br/>+ pgvector 0.8.1)]

        subgraph "Database Tables"
            INVOICES[Invoices<br/>+ Vector Embeddings]
            VENDORS[Vendors]
            LINE_ITEMS[Line Items]
            CACHE[Parse Cache]
        end
    end

    subgraph "External Storage"
        PDFS[PDF Files<br/>/tmp/uploads]
        HF_CACHE[Hugging Face Cache<br/>~/.cache/huggingface]
    end

    %% User flows
    UI -->|HTTP| FASTAPI
    API_DOCS -->|HTTP| FASTAPI

    %% API routing
    FASTAPI --> UPLOAD
    FASTAPI --> SEARCH
    FASTAPI --> SIMILAR
    FASTAPI --> ANALYTICS
    FASTAPI --> CHAT

    %% Service connections
    UPLOAD --> PARSER
    PARSER --> NEAR_AI
    PARSER --> EMBEDDINGS
    PARSER --> NORMALIZER

    SEARCH --> EMBEDDINGS
    SIMILAR --> POSTGRES
    CHAT --> NEAR_AI

    %% Embedding flow
    EMBEDDINGS --> BGE
    EMBEDDINGS -.->|Fallback| FALLBACK
    BGE -.->|Downloads on first use| HF_CACHE

    %% Data persistence
    PARSER --> POSTGRES
    PARSER --> PDFS
    POSTGRES --> INVOICES
    POSTGRES --> VENDORS
    POSTGRES --> LINE_ITEMS
    POSTGRES --> CACHE

    %% Styling
    classDef userInterface fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef application fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef ai fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class UI,API_DOCS userInterface
    class FASTAPI,UPLOAD,SEARCH,SIMILAR,ANALYTICS,CHAT application
    class PARSER,EMBEDDINGS,NEAR_AI,NORMALIZER service
    class BGE,FALLBACK ai
    class POSTGRES,PDFS,HF_CACHE storage
```

## Invoice Processing Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit UI
    participant API as FastAPI
    participant Parser as PDF Parser
    participant Cache as Parse Cache
    participant AI as NEAR AI<br/>(DeepSeek-V3.1)
    participant Embeddings as Embedding Service
    participant BGE as BGE-Large<br/>(Local)
    participant DB as PostgreSQL<br/>+ pgvector

    User->>UI: Upload PDF Invoice
    UI->>API: POST /api/upload
    activate API

    API->>Parser: process_invoice(pdf)
    activate Parser

    %% Step 1: Hash check
    Parser->>Parser: compute_file_hash()
    Parser->>Cache: check_cache(hash)

    alt Cache Hit
        Cache-->>Parser: return cached data
    else Cache Miss - Try invoice2data
        Parser->>Parser: extract_with_invoice2data()

        alt invoice2data Success
            Parser->>Parser: validate_extraction()
        else invoice2data Fails
            %% Fallback to NEAR AI
            Parser->>AI: analyze_invoice(pdf_text)
            AI-->>Parser: extracted_fields (JSON)
            Parser->>Parser: validate_extraction()
        end

        Parser->>Cache: save_to_cache(hash, data)
    end

    %% Step 2: Generate Embedding
    Parser->>Embeddings: generate_invoice_embedding()
    activate Embeddings

    Embeddings->>Embeddings: build_text_representation()
    Note over Embeddings: Vendor: X<br/>Category: Y<br/>Amount: $Z<br/>Date: ...

    Embeddings->>BGE: encode(text)
    activate BGE
    BGE-->>Embeddings: [0.1, 0.2, ..., 0.9]<br/>(1024 dimensions)
    deactivate BGE

    Embeddings-->>Parser: embedding_vector
    deactivate Embeddings

    %% Step 3: Save to database
    Parser->>DB: INSERT INTO invoices<br/>(vendor, amount, embedding, ...)
    Parser->>DB: UPDATE vendors<br/>(total_spent, invoice_count, ...)

    DB-->>Parser: invoice_id
    Parser-->>API: {invoice_id, status: "complete"}
    deactivate Parser

    API-->>UI: {invoice_id, vendor, amount, ...}
    deactivate API
    UI-->>User: Display parsed invoice

    %% Semantic Search Flow
    rect rgb(240, 248, 255)
        Note over User,DB: Semantic Search Example
        User->>UI: Search "cloud computing"
        UI->>API: GET /api/search/semantic?query=...
        API->>Embeddings: generate_embedding(query, is_query=True)

        Embeddings->>BGE: encode("Represent this sentence...<br/>cloud computing")
        BGE-->>Embeddings: query_embedding
        Embeddings-->>API: query_embedding

        API->>DB: SELECT * FROM invoices<br/>ORDER BY embedding <=> query_embedding<br/>LIMIT 10
        Note over DB: Uses pgvector<br/>cosine distance

        DB-->>API: [AWS, Azure, GCP, ...]<br/>+ similarity_scores
        API-->>UI: search_results
        UI-->>User: Display similar invoices
    end
```

## Data Flow: Semantic Search

```mermaid
flowchart LR
    subgraph "Query Input"
        Q[User Query:<br/>"cloud computing"]
    end

    subgraph "Query Processing"
        PREFIX[Add BGE Prefix:<br/>"Represent this sentence<br/>for searching relevant passages:<br/>cloud computing"]
        Q_EMB[Generate Embedding<br/>BGE-Large]
        Q_VEC[[Query Vector<br/>1024 dimensions]]
    end

    subgraph "Database Search"
        PGVECTOR[(pgvector<br/>PostgreSQL 17)]
        COSINE[Cosine Distance<br/>Calculation]
        RANK[Rank by Similarity]
    end

    subgraph "Invoice Embeddings"
        INV1[AWS Invoice<br/>embedding]
        INV2[Azure Invoice<br/>embedding]
        INV3[GCP Invoice<br/>embedding]
        INV4[LinkedIn Invoice<br/>embedding]
    end

    subgraph "Results"
        R1["1. AWS (0.95)"]
        R2["2. Azure (0.92)"]
        R3["3. GCP (0.89)"]
    end

    Q --> PREFIX
    PREFIX --> Q_EMB
    Q_EMB --> Q_VEC
    Q_VEC --> PGVECTOR

    PGVECTOR --> INV1
    PGVECTOR --> INV2
    PGVECTOR --> INV3
    PGVECTOR --> INV4

    INV1 & INV2 & INV3 & INV4 --> COSINE
    COSINE --> RANK

    RANK --> R1
    RANK --> R2
    RANK --> R3

    style PREFIX fill:#e8f5e9
    style Q_EMB fill:#e8f5e9
    style Q_VEC fill:#c8e6c9
    style COSINE fill:#fff3e0
    style R1 fill:#e1f5ff
    style R2 fill:#e1f5ff
    style R3 fill:#e1f5ff
```

## Technology Stack

### Frontend
- **Streamlit 1.29.0** - Dashboard UI
- **Plotly** - Interactive charts and visualizations

### Backend
- **FastAPI 0.104.1** - REST API framework
- **Uvicorn 0.24.0** - ASGI server
- **SQLAlchemy 2.0.23** - ORM
- **Alembic 1.12.1** - Database migrations

### Database
- **PostgreSQL 17** - Primary database
- **pgvector 0.8.1** - Vector similarity search
- **1024-dimension vectors** - BGE-Large embeddings

### AI/ML
- **NEAR AI** - DeepSeek-V3.1 for invoice parsing
- **BGE-Large** - Local embeddings (BAAI/bge-large-en-v1.5)
- **sentence-transformers 5.1.2** - Embedding framework
- **invoice2data 0.4.4** - Template-based parser (fallback)

### PDF Processing
- **pdfplumber 0.10.3** - PDF text extraction
- **PyPDF2 3.0.1** - PDF utilities

### Security & Validation
- **python-magic** - File type verification
- **Pydantic 2.5.2** - Data validation
- **CORS middleware** - Origin whitelisting

## Deployment Considerations

### Privacy & Data Security
- **100% Local Embeddings** - BGE model runs entirely on your infrastructure
- **No Data Leaks** - Invoice data never sent to external embedding APIs
- **Optional OpenAI Fallback** - Can switch providers via `EMBEDDING_PROVIDER` env var

### Performance
- **Model Caching** - BGE model loaded once per server instance (singleton)
- **Parse Caching** - PDF extractions cached by file hash
- **Vector Indexing** - pgvector uses HNSW for fast similarity search
- **Connection Pooling** - SQLAlchemy manages database connections

### Scalability
- **Async Processing** - FastAPI async endpoints for concurrent requests
- **Batch Embedding** - Can process multiple invoices in parallel
- **Database Migrations** - Alembic handles schema evolution
- **Horizontal Scaling** - Stateless API design allows multiple instances

## Environment Variables

```bash
# Required
NEAR_AI_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@localhost/invoice_db

# Optional (with defaults)
EMBEDDING_PROVIDER=bge              # "bge" (local) or "openai" (API)
OPENAI_API_KEY=                     # Only needed if EMBEDDING_PROVIDER=openai
ENVIRONMENT=development             # "development" or "production"
STREAMLIT_PORT=8501
FASTAPI_PORT=8000
```

## API Endpoints

### Invoice Management
- `POST /api/upload` - Upload and process invoice PDF
- `GET /api/invoices` - List all invoices (paginated)
- `GET /api/invoices/{id}` - Get invoice details
- `DELETE /api/invoices/{id}` - Delete invoice

### Semantic Search (NEW)
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
- `GET /api/status/{job_id}` - Check processing status

## Database Schema

```sql
-- Invoices with vector embeddings
CREATE TABLE invoices (
    id UUID PRIMARY KEY,
    vendor_name VARCHAR(255) NOT NULL,
    vendor_normalized VARCHAR(255) NOT NULL,
    invoice_number VARCHAR(100),
    date DATE NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL,
    category VARCHAR(100) DEFAULT 'Other',
    purchaser VARCHAR(100),
    is_recurring BOOLEAN DEFAULT FALSE,
    pdf_path VARCHAR(500) NOT NULL,
    pdf_hash VARCHAR(64) NOT NULL,
    parsed_at TIMESTAMP DEFAULT NOW(),
    confidence_score FLOAT,
    parser_used VARCHAR(50) NOT NULL,
    parser_version VARCHAR(20),
    embedding vector(1024),  -- pgvector for semantic search

    INDEX idx_vendor_normalized (vendor_normalized),
    INDEX idx_date (date),
    INDEX idx_pdf_hash (pdf_hash),
    INDEX idx_category (category)
);

-- Vendor aggregates
CREATE TABLE vendors (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100) DEFAULT 'Other',
    total_spent NUMERIC(12,2) DEFAULT 0,
    invoice_count INTEGER DEFAULT 0,
    first_seen DATE,
    last_seen DATE
);

-- Line items
CREATE TABLE line_items (
    id UUID PRIMARY KEY,
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity NUMERIC(10,2),
    unit_price NUMERIC(10,2),
    total NUMERIC(10,2) NOT NULL
);
```

---

**Last Updated:** 2025-11-22
**Version:** 2.0.0 (with pgvector semantic search)
