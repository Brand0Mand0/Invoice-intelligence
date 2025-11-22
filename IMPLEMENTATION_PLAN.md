# pgvector + Semantic Search Implementation Plan

## Overview
Add semantic search capabilities to Invoice Intelligence using pgvector for vector embeddings and similarity search.

---

## Phase 1: Database Setup (Step 1-2)

### Step 1: Install pgvector Extension
```sql
-- Connect to PostgreSQL
psql -d invoice_db

-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Step 2: Create Migration for Embedding Column
```bash
# Create Alembic migration
alembic revision -m "add_vector_embedding_column"

# Migration will:
# 1. Add embedding column: vector(1536) for OpenAI ada-002
# 2. Create index for fast similarity search
```

**Migration SQL:**
```sql
ALTER TABLE invoices ADD COLUMN embedding vector(1536);
CREATE INDEX ON invoices USING ivfflat (embedding vector_cosine_ops);
```

---

## Phase 2: Embeddings Service (Step 3-4)

### Step 3: Create Embeddings Service
**File:** `app/services/embeddings.py`

**Responsibilities:**
- Generate embeddings from invoice text
- Support multiple providers (OpenAI, NEAR AI)
- Cache embeddings to avoid regeneration

**Key Functions:**
```python
async def generate_embedding(text: str) -> List[float]
async def generate_invoice_embedding(invoice: Invoice) -> List[float]
```

**Invoice Text Representation:**
```python
# Combine key fields for semantic meaning
text = f"""
Vendor: {invoice.vendor_name}
Category: {invoice.category}
Amount: ${invoice.total_amount}
Date: {invoice.date}
Invoice Number: {invoice.invoice_number}
Recurring: {'Yes' if invoice.is_recurring else 'No'}
"""
```

### Step 4: Add pgvector to Dependencies
```bash
pip install pgvector
pip install openai  # For embeddings API
```

**Update:** `requirements.txt`

---

## Phase 3: Integration (Step 5-6)

### Step 5: Update Parser to Generate Embeddings
**File:** `app/services/parser.py`

**Changes:**
```python
from app.services.embeddings import generate_invoice_embedding

async def process(self, pdf_path: str):
    # ... existing extraction logic ...

    # Generate embedding AFTER invoice is created
    embedding = await generate_invoice_embedding(invoice)
    invoice.embedding = embedding
    db.commit()
```

### Step 6: Create Semantic Search Endpoint
**File:** `app/api/routes/invoices.py`

**New Endpoints:**
```python
@router.get("/search/semantic")
async def semantic_search(query: str, limit: int = 10)

@router.get("/{invoice_id}/similar")
async def find_similar_invoices(invoice_id: str, limit: int = 5)
```

**Vector Similarity Query:**
```python
# Find invoices by semantic similarity
results = db.query(Invoice).order_by(
    Invoice.embedding.cosine_distance(query_embedding)
).limit(limit).all()
```

---

## Phase 4: Testing (Step 7)

### Step 7: Test with Sample Invoices
1. Upload diverse invoices (software, hardware, services)
2. Test semantic search:
   - "software subscriptions"
   - "cloud computing costs"
   - "recurring monthly expenses"
3. Test similar invoice finder
4. Verify results make semantic sense

---

## Technical Details

### Embedding Model
**OpenAI text-embedding-ada-002:**
- Dimension: 1536
- Cost: $0.0001 per 1K tokens
- Quality: High
- Speed: ~500ms per request

**Alternative (NEAR AI):**
- Check if NEAR AI has embeddings endpoint
- If not, use OpenAI for embeddings only

### Vector Index
**IVFFlat Index:**
- Fast approximate nearest neighbor search
- Good for 10K-1M vectors
- Creates 100 centroids by default

```sql
CREATE INDEX ON invoices
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Distance Metrics
- **Cosine Distance:** Recommended for text embeddings
- **L2 Distance:** Alternative
- **Inner Product:** For normalized vectors

**Example:**
```python
# Cosine similarity (0-2, lower is more similar)
Invoice.embedding.cosine_distance(query_embedding)

# L2 distance
Invoice.embedding.l2_distance(query_embedding)
```

---

## File Structure

```
app/
├── services/
│   ├── embeddings.py          # 🆕 NEW - Generate embeddings
│   └── parser.py              # ✏️ MODIFIED - Add embedding generation
├── api/routes/
│   └── invoices.py            # ✏️ MODIFIED - Add semantic search
└── models/
    └── invoice.py             # ✏️ MODIFIED - Add embedding column

migrations/
└── versions/
    └── add_vector_embedding.py # 🆕 NEW - Database migration

requirements.txt               # ✏️ MODIFIED - Add pgvector, openai
```

---

## Success Criteria

### Functional Requirements:
- ✅ Embeddings generated automatically on invoice upload
- ✅ Semantic search returns relevant results
- ✅ "Find similar" feature works for any invoice
- ✅ Results ranked by similarity score

### Performance Requirements:
- ⚡ Embedding generation: < 1 second
- ⚡ Semantic search: < 500ms for 10K invoices
- ⚡ Similar invoice lookup: < 300ms

### Quality Requirements:
- 🎯 Semantic search finds "software subscriptions" for query "SaaS costs"
- 🎯 Similar invoices share category/vendor even with different names
- 🎯 Recurring patterns recognized semantically

---

## Future Enhancements (Not in Scope)

### Phase 2 (Later):
- LangChain integration for RAG chat
- Multi-modal embeddings (include PDF images)
- Hybrid search (semantic + keyword)
- Embedding fine-tuning on invoice data

### Phase 3 (Future):
- Graph RAG (if needed)
- Real-time embedding updates
- Batch embedding generation
- Embedding cache layer (Redis)

---

## Rollback Plan

If issues arise:
```sql
-- Remove extension
DROP EXTENSION vector CASCADE;

-- Remove column
ALTER TABLE invoices DROP COLUMN embedding;
```

**Safe because:**
- Embeddings are derived data (can be regenerated)
- Original invoice data unchanged
- Existing features continue working

---

## Estimated Timeline

| Task | Estimated Time | Status |
|------|----------------|--------|
| Install pgvector extension | 10 min | ⏳ Pending |
| Create migration | 20 min | ⏳ Pending |
| Create embeddings service | 2 hours | ⏳ Pending |
| Update parser | 30 min | ⏳ Pending |
| Create semantic search endpoint | 1 hour | ⏳ Pending |
| Testing | 1 hour | ⏳ Pending |
| **Total** | **~5 hours** | |

---

## Next Steps

1. ✅ Database cleared
2. ✅ Plan created
3. ⏳ Install pgvector extension
4. ⏳ Create migration
5. ⏳ Implement embeddings service
6. ⏳ Test semantic search

**Ready to start Step 1!**
