"""Incident service — business logic for incident CRUD and statistics."""
from datetime import datetime, timezone
from app.extensions import db
from app.models.incident import Incident
from app.models.incident_comment import IncidentComment
from app.services import audit_service
from app.services import notification_service


def get_all_incidents(filters: dict = None) -> list:
    """Return all incidents, optionally filtered."""
    query = Incident.query
    if filters:
        if filters.get('status'):
            query = query.filter(Incident.status == filters['status'])
        if filters.get('severity'):
            query = query.filter(Incident.severity == filters['severity'])
        if filters.get('category_id'):
            query = query.filter(Incident.category_id == int(filters['category_id']))
        if filters.get('search'):
            term = f"%{filters['search']}%"
            query = query.filter(
                db.or_(Incident.title.ilike(term), Incident.description.ilike(term))
            )
    return query.order_by(Incident.created_at.desc()).all()


def get_incident_by_id(incident_id: int):
    """Return an Incident or None."""
    return db.session.get(Incident, incident_id)


def create_incident(data: dict, current_user, ip_address: str = None) -> Incident:
    """Create a new incident and write an audit log entry."""
    incident = Incident(
        title=data['title'],
        description=data.get('description', ''),
        category_id=data.get('category_id') or None,
        severity=data.get('severity', 'medium'),
        status='open',
        reported_by=current_user.id,
    )
    db.session.add(incident)
    db.session.flush()  # populate incident.id before audit

    audit_service.log_action(
        user_id=current_user.id,
        table_name='incidents',
        record_id=incident.id,
        action='CREATE',
        new_values=incident.to_dict(),
        ip_address=ip_address,
    )

    db.session.commit()

    # Send an out-of-band alert for very severe incidents.
    alert_severity = (data.get('severity') or 'medium').lower()
    configured_severity = 'critical'
    try:
        from flask import current_app
        configured_severity = str(current_app.config.get('INCIDENT_ALERT_SEVERITY', 'critical')).lower()
    except Exception:
        configured_severity = 'critical'

    if alert_severity == configured_severity:
        notification_service.send_critical_incident_email(
            incident=incident,
            reporter_name=getattr(current_user, 'name', 'Unknown Reporter'),
        )

    return incident


def update_incident(incident: Incident, data: dict, current_user, ip_address: str = None) -> Incident:
    """Update an existing incident and write an audit log entry."""
    old_values = incident.to_dict()

    for field in ('title', 'description', 'category_id', 'severity', 'status', 'assigned_to'):
        if field in data:
            value = data[field]
            # Treat 0 as "unset" for FK fields
            if field in ('category_id', 'assigned_to') and value == 0:
                value = None
            setattr(incident, field, value)

    # Track resolution timestamp
    if incident.status == 'resolved' and not incident.resolved_at:
        incident.resolved_at = datetime.now(timezone.utc)
    elif incident.status not in ('resolved', 'closed'):
        incident.resolved_at = None

    incident.updated_at = datetime.now(timezone.utc)

    audit_service.log_action(
        user_id=current_user.id,
        table_name='incidents',
        record_id=incident.id,
        action='UPDATE',
        old_values=old_values,
        new_values=incident.to_dict(),
        ip_address=ip_address,
    )

    db.session.commit()
    return incident


def delete_incident(incident: Incident, current_user, ip_address: str = None) -> None:
    """Delete an incident and write an audit log entry."""
    old_values = incident.to_dict()
    incident_id = incident.id

    audit_service.log_action(
        user_id=current_user.id,
        table_name='incidents',
        record_id=incident_id,
        action='DELETE',
        old_values=old_values,
        ip_address=ip_address,
    )

    db.session.delete(incident)
    db.session.commit()


def add_comment(incident: Incident, comment_text: str, current_user) -> IncidentComment:
    """Add a comment to an incident."""
    comment = IncidentComment(
        incident_id=incident.id,
        user_id=current_user.id,
        comment=comment_text,
    )
    db.session.add(comment)
    db.session.commit()
    return comment


def get_stats() -> dict:
    """Return aggregate incident counts for dashboard/monitoring."""
    return {
        'total': Incident.query.count(),
        'open': Incident.query.filter_by(status='open').count(),
        'in_progress': Incident.query.filter_by(status='in_progress').count(),
        'resolved': Incident.query.filter_by(status='resolved').count(),
        'closed': Incident.query.filter_by(status='closed').count(),
        'critical': Incident.query.filter_by(severity='critical').count(),
        'high': Incident.query.filter_by(severity='high').count(),
    }
