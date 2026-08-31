"""Audit service — append-only audit log for all data mutations."""
from app.extensions import db
from app.models.audit_log import AuditLog


def log_action(
    user_id,
    table_name: str,
    record_id: int,
    action: str,
    old_values: dict = None,
    new_values: dict = None,
    ip_address: str = None,
) -> AuditLog:
    """
    Append an entry to the audit log.

    NOTE: Does NOT commit the session — the caller must commit after calling
    this so that the audit entry and the data change are in the same transaction.
    """
    entry = AuditLog(
        user_id=user_id,
        table_name=table_name,
        record_id=record_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
    )
    db.session.add(entry)
    return entry
