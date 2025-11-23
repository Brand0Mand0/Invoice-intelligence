from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.api.deps import get_db
from app.models.invoice import Invoice, LineItem
from app.services.embeddings import generate_embedding
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/invoices")
def get_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of all invoices."""
    invoices = db.query(Invoice).offset(skip).limit(limit).all()

    return {
        "invoices": [
            {
                "id": str(inv.id),
                "vendor_name": inv.vendor_name,
                "vendor_normalized": inv.vendor_normalized,
                "invoice_number": inv.invoice_number,
                "date": inv.date.isoformat() if inv.date else None,
                "total_amount": float(inv.total_amount),
                "category": inv.category,
                "purchaser": inv.purchaser,
                "is_recurring": inv.is_recurring,
                "confidence_score": inv.confidence_score,
                "parser_used": inv.parser_used,
                "parsed_at": inv.parsed_at.isoformat() if inv.parsed_at else None,
            }
            for inv in invoices
        ],
        "total": db.query(Invoice).count()
    }


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """Get detailed invoice with line items."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return {
        "id": str(invoice.id),
        "vendor_name": invoice.vendor_name,
        "vendor_normalized": invoice.vendor_normalized,
        "invoice_number": invoice.invoice_number,
        "date": invoice.date.isoformat() if invoice.date else None,
        "total_amount": float(invoice.total_amount),
        "category": invoice.category,
        "purchaser": invoice.purchaser,
        "is_recurring": invoice.is_recurring,
        "confidence_score": invoice.confidence_score,
        "parser_used": invoice.parser_used,
        "line_items": [
            {
                "id": str(item.id),
                "description": item.description,
                "quantity": float(item.quantity) if item.quantity else None,
                "unit_price": float(item.unit_price) if item.unit_price else None,
                "total": float(item.total),
            }
            for item in invoice.line_items
        ]
    }


@router.get("/vendors")
def get_vendors(db: Session = Depends(get_db)):
    """Get list of all vendors with aggregated data."""
    from app.models.vendor import Vendor

    vendors = db.query(Vendor).all()

    return {
        "vendors": [
            {
                "id": str(vendor.id),
                "name": vendor.name,
                "normalized_name": vendor.normalized_name,
                "category": vendor.category,
                "total_spent": float(vendor.total_spent),
                "invoice_count": vendor.invoice_count,
                "first_seen": vendor.first_seen.isoformat() if vendor.first_seen else None,
                "last_seen": vendor.last_seen.isoformat() if vendor.last_seen else None,
            }
            for vendor in vendors
        ]
    }


@router.get("/search/semantic")
async def semantic_search(
    query: str = Query(..., description="Natural language search query"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Semantic search for invoices using natural language queries.

    Examples:
    - "software subscriptions"
    - "cloud computing expenses"
    - "recurring monthly charges"
    - "office supplies under $50"

    Uses vector similarity to find conceptually related invoices.
    """
    logger.info(
        "Semantic search request",
        extra={"extra_data": {"query": query, "limit": limit}}
    )

    try:
        # Generate embedding for the search query (with BGE instruction prefix)
        query_embedding = await generate_embedding(query, is_query=True)

        # Find similar invoices using cosine distance
        # <=> is the cosine distance operator in pgvector
        results = db.query(
            Invoice,
            Invoice.embedding.cosine_distance(query_embedding).label("distance")
        ).filter(
            Invoice.embedding.isnot(None)  # Only invoices with embeddings
        ).order_by(
            "distance"  # Closest matches first (lower distance = more similar)
        ).limit(limit).all()

        logger.info(
            "Semantic search completed",
            extra={"extra_data": {"query": query, "results_count": len(results)}}
        )

        return {
            "query": query,
            "results": [
                {
                    "id": str(inv.id),
                    "vendor_name": inv.vendor_name,
                    "vendor_normalized": inv.vendor_normalized,
                    "invoice_number": inv.invoice_number,
                    "date": inv.date.isoformat() if inv.date else None,
                    "total_amount": float(inv.total_amount),
                    "category": inv.category,
                    "purchaser": inv.purchaser,
                    "is_recurring": inv.is_recurring,
                    "similarity_score": 1 - distance,  # Convert distance to similarity (0-1)
                    "confidence_score": inv.confidence_score,
                }
                for inv, distance in results
            ],
            "total": len(results)
        }

    except Exception as e:
        logger.error(
            "Semantic search failed",
            exc_info=True,
            extra={"extra_data": {"query": query, "error": str(e)}}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.get("/invoices/{invoice_id}/similar")
async def find_similar_invoices(
    invoice_id: str,
    limit: int = Query(5, ge=1, le=50, description="Number of similar invoices to return"),
    db: Session = Depends(get_db)
):
    """
    Find invoices similar to a specific invoice.

    Uses vector similarity to find invoices with similar characteristics
    (vendor type, category, amount range, etc.)
    """
    # Get the target invoice
    target_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not target_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if target_invoice.embedding is None:
        raise HTTPException(
            status_code=400,
            detail="Target invoice does not have an embedding. Try reprocessing the invoice."
        )

    logger.info(
        "Find similar invoices request",
        extra={
            "extra_data": {
                "target_invoice_id": invoice_id,
                "vendor": target_invoice.vendor_normalized,
                "limit": limit
            }
        }
    )

    try:
        # Find similar invoices using cosine distance
        results = db.query(
            Invoice,
            Invoice.embedding.cosine_distance(target_invoice.embedding).label("distance")
        ).filter(
            Invoice.embedding.isnot(None),
            Invoice.id != invoice_id  # Exclude the target invoice itself
        ).order_by(
            "distance"
        ).limit(limit).all()

        logger.info(
            "Find similar invoices completed",
            extra={"extra_data": {"target_invoice_id": invoice_id, "results_count": len(results)}}
        )

        return {
            "target_invoice": {
                "id": str(target_invoice.id),
                "vendor_name": target_invoice.vendor_name,
                "vendor_normalized": target_invoice.vendor_normalized,
                "category": target_invoice.category,
                "total_amount": float(target_invoice.total_amount),
            },
            "similar_invoices": [
                {
                    "id": str(inv.id),
                    "vendor_name": inv.vendor_name,
                    "vendor_normalized": inv.vendor_normalized,
                    "invoice_number": inv.invoice_number,
                    "date": inv.date.isoformat() if inv.date else None,
                    "total_amount": float(inv.total_amount),
                    "category": inv.category,
                    "purchaser": inv.purchaser,
                    "is_recurring": inv.is_recurring,
                    "similarity_score": 1 - distance,
                    "confidence_score": inv.confidence_score,
                }
                for inv, distance in results
            ],
            "total": len(results)
        }

    except Exception as e:
        logger.error(
            "Find similar invoices failed",
            exc_info=True,
            extra={"extra_data": {"target_invoice_id": invoice_id, "error": str(e)}}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find similar invoices: {str(e)}"
        )
