"""IncidentComment model."""
from datetime import datetime, timezone
from app.extensions import db


class IncidentComment(db.Model):
    __tablename__ = 'incident_comments'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    author = db.relationship('User', backref='comments')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'user_id': self.user_id,
            'author_name': self.author.name if self.author else None,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f'<Comment {self.id} on Incident {self.incident_id}>'
