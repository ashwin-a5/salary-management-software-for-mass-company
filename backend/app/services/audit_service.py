from sqlalchemy.orm import Session
from app.models import AuditLog, User
from typing import Optional

def log_activity(
    db: Session,
    action: str,
    module: str,
    user: Optional[User] = None,
    record_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = "127.0.0.1"
):
    try:
        log_entry = AuditLog(
            user_id=user.id if user else None,
            user_email=user.email if user else "system",
            role=user.role if user else "system",
            action=action,
            module=module,
            record_id=str(record_id) if record_id is not None else None,
            details=details,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to write audit log: {e}")
