from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.api.deps import get_db
from app.models.invoice import Invoice, LineItem

router = APIRouter()


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
