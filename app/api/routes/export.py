from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io
from app.api.deps import get_db
from app.models.invoice import Invoice

router = APIRouter()


@router.get("/export/csv")
def export_invoices_csv(db: Session = Depends(get_db)):
    """Export all invoices to CSV file."""
    invoices = db.query(Invoice).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Invoice ID",
        "Vendor",
        "Vendor (Normalized)",
        "Invoice Number",
        "Date",
        "Total Amount",
        "Confidence Score",
        "Parser Used",
        "Parsed At"
    ])

    # Write data
    for inv in invoices:
        writer.writerow([
            str(inv.id),
            inv.vendor_name,
            inv.vendor_normalized,
            inv.invoice_number or "",
            inv.date.isoformat() if inv.date else "",
            float(inv.total_amount),
            inv.confidence_score or "",
            inv.parser_used,
            inv.parsed_at.isoformat() if inv.parsed_at else ""
        ])

    # Prepare response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices.csv"}
    )
