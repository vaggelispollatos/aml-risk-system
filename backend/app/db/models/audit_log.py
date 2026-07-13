"""Audit log — immutable record of every system action."""

from sqlalchemy import Column, JSON, String, Text

from app.db.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # create, update, delete, review

    performed_by = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)

    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    details = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.entity_type}:{self.action}>"