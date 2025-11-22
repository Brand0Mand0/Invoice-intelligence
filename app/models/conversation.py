import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Conversation(Base):
    """Chat conversation history with NEAR AI."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model_used = Column(String(50), nullable=False)  # e.g., 'zai-org/GLM-4.6'
    completion_id = Column(String(100))  # Chat completion ID for TEE verification
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<Conversation {self.id} - {self.model_used}>"
