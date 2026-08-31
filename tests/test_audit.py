"""Tests for the audit logging service."""
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services import audit_service, incident_service


class TestAuditService:
    def test_log_action_creates_entry(self, app):
        with app.app_context():
            from app.extensions import db
            count_before = AuditLog.query.count()
            audit_service.log_action(
                user_id=1,
                table_name='test_table',
                record_id=999,
                action='CREATE',
                new_values={'key': 'value'},
                ip_address='127.0.0.1',
            )
            db.session.commit()
            assert AuditLog.query.count() == count_before + 1

    def test_log_action_stores_correct_data(self, app):
        with app.app_context():
            from app.extensions import db
            entry = audit_service.log_action(
                user_id=1,
                table_name='incidents',
                record_id=42,
                action='UPDATE',
                old_values={'status': 'open'},
                new_values={'status': 'resolved'},
                ip_address='10.0.0.1',
            )
            db.session.commit()
            db.session.refresh(entry)
            assert entry.action == 'UPDATE'
            assert entry.old_values['status'] == 'open'
            assert entry.new_values['status'] == 'resolved'
            assert entry.ip_address == '10.0.0.1'


class TestAuditIntegration:
    def test_create_incident_writes_audit(self, app):
        with app.app_context():
            user = User.query.filter_by(email='user@test.com').first()
            count_before = AuditLog.query.count()

            incident = incident_service.create_incident(
                data={'title': 'Audit Integration Test', 'severity': 'low'},
                current_user=user,
                ip_address='127.0.0.1',
            )

            assert AuditLog.query.count() == count_before + 1
            # Use .order_by(id desc) to get the most-recent CREATE entry
            # (earlier tests may have created-then-deleted incidents whose
            # SQLite IDs get recycled)
            log = AuditLog.query.filter_by(
                table_name='incidents',
                record_id=incident.id,
                action='CREATE',
            ).order_by(AuditLog.id.desc()).first()
            assert log is not None
            assert log.user_id == user.id
            assert log.new_values['title'] == 'Audit Integration Test'

    def test_update_incident_writes_audit(self, app):
        with app.app_context():
            user = User.query.filter_by(email='user@test.com').first()
            incident = incident_service.create_incident(
                data={'title': 'Update Audit Test', 'severity': 'medium'},
                current_user=user,
            )
            count_before = AuditLog.query.count()

            incident_service.update_incident(
                incident,
                data={'title': 'Update Audit Test — edited'},
                current_user=user,
            )

            assert AuditLog.query.count() == count_before + 1
            log = AuditLog.query.filter_by(
                table_name='incidents',
                record_id=incident.id,
                action='UPDATE',
            ).first()
            assert log is not None
            assert log.old_values['title'] == 'Update Audit Test'
            assert log.new_values['title'] == 'Update Audit Test — edited'

    def test_delete_incident_writes_audit(self, app):
        with app.app_context():
            user = User.query.filter_by(email='user@test.com').first()
            incident = incident_service.create_incident(
                data={'title': 'Delete Audit Test', 'severity': 'low'},
                current_user=user,
            )
            incident_id = incident.id
            count_before = AuditLog.query.count()

            incident_service.delete_incident(incident, current_user=user)

            assert AuditLog.query.count() == count_before + 1
            log = AuditLog.query.filter_by(
                table_name='incidents',
                record_id=incident_id,
                action='DELETE',
            ).first()
            assert log is not None
