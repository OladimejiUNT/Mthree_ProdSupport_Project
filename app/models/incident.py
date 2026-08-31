"""Incident model — core entity of the application."""
from datetime import datetime, timezone
from app.extensions import db


class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    severity = db.Column(
        db.Enum('low', 'medium', 'high', 'critical'),
        nullable=False,
        default='medium',
    )
    status = db.Column(
        db.Enum('open', 'in_progress', 'resolved', 'closed'),
        nullable=False,
        default='open',
    )
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    category = db.relationship('Category', backref=db.backref('incidents', lazy='dynamic'))
    reporter = db.relationship('User', foreign_keys=[reported_by], backref='reported_incidents')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_incidents')
    comments = db.relationship(
        'IncidentComment',
        backref='incident',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'category': self.category.name if self.category else None,
            'severity': self.severity,
            'status': self.status,
            'reported_by': self.reported_by,
            'reporter_name': self.reporter.name if self.reporter else None,
            'assigned_to': self.assigned_to,
            'assignee_name': self.assignee.name if self.assignee else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
        }

    def __repr__(self) -> str:
        return f'<Incident #{self.id}: {self.title}>'
