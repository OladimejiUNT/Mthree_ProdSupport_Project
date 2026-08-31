"""UserSession model — server-side session tracking."""
from datetime import datetime, timezone
from app.extensions import db


class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref='sessions')

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self) -> str:
        return f'<UserSession {self.id} for User {self.user_id}>'
