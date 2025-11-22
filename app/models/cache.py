from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class ParseCache(Base):
    """Cache for parsed PDF data to prevent re-processing."""

    __tablename__ = "parse_cache"

    cache_key = Column(String(100), primary_key=True)  # pdf_hash + parser_version
    extracted_data = Column(JSONB, nullable=False)
    confidence = Column(Float)
    parser_used = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ParseCache {self.cache_key} - {self.parser_used}>"
