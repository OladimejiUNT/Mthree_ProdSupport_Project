"""Admin controller — admin-only views for users, audit log, and dashboard."""
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services import incident_service

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator: 403 if the current user is not an admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = incident_service.get_stats()
    recent_audits = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_audits=recent_audits,
                           total_users=total_users,
                           active_users=active_users)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    action = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.name} has been {action}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@login_required
@admin_required
def toggle_user_role(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'danger')
        return redirect(url_for('admin.users'))
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    flash(f'{user.name} is now a {user.role}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    page = request.args.get('page', 1, type=int)
    logs = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .paginate(page=page, per_page=25, error_out=False)
    )
    return render_template('admin/audit_log.html', logs=logs)
