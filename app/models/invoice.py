import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, Float, ForeignKey, Text, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Invoice(Base):
    """Invoice entity with parsed data and metadata."""

    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_name = Column(String(255), nullable=False)
    vendor_normalized = Column(String(255), nullable=False, index=True)
    invoice_number = Column(String(100))
    date = Column(Date, nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Business intelligence fields
    category = Column(String(100), index=True, default="Other")  # e.g., "Software/SaaS", "Office Supplies", etc.
    purchaser = Column(String(100))  # Who made the purchase (extracted from invoice or set by user)
    is_recurring = Column(Boolean, default=False)  # Is this a subscription/recurring charge?

    pdf_path = Column(String(500), nullable=False)
    pdf_hash = Column(String(64), nullable=False, index=True)
    parsed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence_score = Column(Float)
    parser_used = Column(String(50), nullable=False)  # 'invoice2data' | 'deepseek' | 'glm-4.6'
    parser_version = Column(String(20))

    # Relationships
    line_items = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.vendor_normalized} - {self.category} - ${self.total_amount}>"


class LineItem(Base):
    """Line item within an invoice."""

    __tablename__ = "line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 2))
    unit_price = Column(Numeric(10, 2))
    total = Column(Numeric(10, 2), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")

    def __repr__(self):
        return f"<LineItem {self.description[:30]} - ${self.total}>"
