import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class ProcessingJob(Base):
    """Async processing job tracker."""

    __tablename__ = "processing_jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default="queued", index=True)
    # Status values: 'queued' | 'processing' | 'complete' | 'error'
    pdf_path = Column(String(500), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    result = Column(JSONB)
    error_message = Column(Text)

    def __repr__(self):
        return f"<ProcessingJob {self.job_id} - {self.status}>"
