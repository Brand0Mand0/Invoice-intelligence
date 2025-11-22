import uuid
from datetime import date
from sqlalchemy import Column, String, Numeric, Integer, Date
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Vendor(Base):
    """Vendor entity with aggregated metrics."""

    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100))
    total_spent = Column(Numeric(12, 2), default=0, nullable=False)
    invoice_count = Column(Integer, default=0, nullable=False)
    first_seen = Column(Date, nullable=False)
    last_seen = Column(Date, nullable=False)

    def __repr__(self):
        return f"<Vendor {self.normalized_name} - {self.invoice_count} invoices - ${self.total_spent}>"
