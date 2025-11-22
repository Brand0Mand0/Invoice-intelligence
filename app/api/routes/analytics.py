from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.api.deps import get_db
from app.models.invoice import Invoice
from app.models.vendor import Vendor

router = APIRouter()


@router.get("/analytics/monthly")
def get_monthly_analytics(db: Session = Depends(get_db)):
    """Get monthly spending trends."""
    # Query for monthly aggregation
    monthly_data = (
        db.query(
            extract('year', Invoice.date).label('year'),
            extract('month', Invoice.date).label('month'),
            func.sum(Invoice.total_amount).label('total'),
            func.count(Invoice.id).label('count')
        )
        .group_by('year', 'month')
        .order_by('year', 'month')
        .all()
    )

    return {
        "data": [
            {
                "year": int(row.year),
                "month": int(row.month),
                "total": float(row.total),
                "count": row.count
            }
            for row in monthly_data
        ],
        "total": sum(float(row.total) for row in monthly_data)
    }


@router.get("/analytics/top-vendors")
def get_top_vendors(limit: int = 10, db: Session = Depends(get_db)):
    """Get top vendors by spending."""
    vendors = (
        db.query(Vendor)
        .order_by(Vendor.total_spent.desc())
        .limit(limit)
        .all()
    )

    return {
        "vendors": [
            {
                "normalized_name": vendor.normalized_name,
                "total_spent": float(vendor.total_spent),
                "invoice_count": vendor.invoice_count
            }
            for vendor in vendors
        ]
    }


@router.get("/analytics/summary")
def get_summary(db: Session = Depends(get_db)):
    """Get overall analytics summary."""
    total_spent = db.query(func.sum(Invoice.total_amount)).scalar() or 0
    total_invoices = db.query(func.count(Invoice.id)).scalar() or 0
    total_vendors = db.query(func.count(Vendor.id)).scalar() or 0
    avg_invoice = db.query(func.avg(Invoice.total_amount)).scalar() or 0

    return {
        "total_spent": float(total_spent),
        "total_invoices": total_invoices,
        "total_vendors": total_vendors,
        "average_invoice": float(avg_invoice)
    }
