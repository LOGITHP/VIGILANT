import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        event: str,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Create a persistent security audit record."""
        audit_entry = AuditLog(
            user_id=user_id,
            event=event,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )
        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)
        return audit_entry

