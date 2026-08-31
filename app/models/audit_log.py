"""AuditLog model — immutable record of all CREATE/UPDATE/DELETE actions."""
from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.Enum('CREATE', 'UPDATE', 'DELETE'), nullable=False)
    # JSON columns: MySQL/Postgres native JSON; SQLite stores as text
    old_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45), nullable=True)

    actor = db.relationship('User', backref='audit_entries')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'actor_name': self.actor.name if self.actor else 'System',
            'table_name': self.table_name,
            'record_id': self.record_id,
            'action': self.action,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ip_address': self.ip_address,
        }

    def __repr__(self) -> str:
        return f'<AuditLog {self.action} {self.table_name}:{self.record_id}>'
