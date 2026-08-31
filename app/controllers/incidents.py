"""Incidents controller — full CRUD for incidents and comments."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.user import User
from app.services import incident_service
from app.forms.incident_forms import CommentForm, IncidentForm, UpdateIncidentForm

incidents_bp = Blueprint('incidents', __name__)


@incidents_bp.route('/')
@login_required
def index():
    filters = {k: v for k, v in {
        'status': request.args.get('status'),
        'severity': request.args.get('severity'),
        'category_id': request.args.get('category_id'),
        'search': request.args.get('search'),
    }.items() if v}

    incidents = incident_service.get_all_incidents(filters)
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    stats = incident_service.get_stats()

    return render_template('incidents/index.html',
                           incidents=incidents,
                           categories=categories,
                           filters=filters,
                           stats=stats)


@incidents_bp.route('/<int:incident_id>')
@login_required
def detail(incident_id):
    incident = incident_service.get_incident_by_id(incident_id)
    if not incident:
        abort(404)

    comment_form = CommentForm()
    audit_entries = []
    if current_user.is_admin:
        audit_entries = (
            AuditLog.query
            .filter_by(table_name='incidents', record_id=incident_id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    return render_template('incidents/detail.html',
                           incident=incident,
                           comment_form=comment_form,
                           audit_entries=audit_entries)


@incidents_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = IncidentForm()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    form.category_id.choices = [(0, '— Select Category —')] + [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        incident = incident_service.create_incident(
            data={
                'title': form.title.data,
                'description': form.description.data,
                'category_id': form.category_id.data or None,
                'severity': form.severity.data,
            },
            current_user=current_user,
            ip_address=request.remote_addr,
        )
        flash(f'Incident #{incident.id} created successfully.', 'success')
        return redirect(url_for('incidents.detail', incident_id=incident.id))

    return render_template('incidents/create.html', form=form)


@incidents_bp.route('/<int:incident_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(incident_id):
    incident = incident_service.get_incident_by_id(incident_id)
    if not incident:
        abort(404)
    if incident.reported_by != current_user.id and not current_user.is_admin:
        abort(403)

    form = UpdateIncidentForm(obj=incident)
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    form.category_id.choices = [(0, '— None —')] + [(c.id, c.name) for c in categories]
    all_users = User.query.filter_by(is_active=True).order_by(User.name).all()
    form.assigned_to.choices = [(0, '— Unassigned —')] + [(u.id, u.name) for u in all_users]

    if request.method == 'GET':
        form.category_id.data = incident.category_id or 0
        form.assigned_to.data = incident.assigned_to or 0

    if form.validate_on_submit():
        data = {
            'title': form.title.data,
            'description': form.description.data,
            'category_id': form.category_id.data,
            'severity': form.severity.data,
        }
        # Status and assignment are admin-only fields
        if current_user.is_admin:
            data['status'] = form.status.data
            data['assigned_to'] = form.assigned_to.data

        incident_service.update_incident(incident, data, current_user, request.remote_addr)
        flash(f'Incident #{incident.id} updated.', 'success')
        return redirect(url_for('incidents.detail', incident_id=incident.id))

    return render_template('incidents/edit.html', form=form, incident=incident)


@incidents_bp.route('/<int:incident_id>/delete', methods=['POST'])
@login_required
def delete(incident_id):
    incident = incident_service.get_incident_by_id(incident_id)
    if not incident:
        abort(404)
    if incident.reported_by != current_user.id and not current_user.is_admin:
        abort(403)

    incident_service.delete_incident(incident, current_user, request.remote_addr)
    flash('Incident deleted.', 'success')
    return redirect(url_for('incidents.index'))


@incidents_bp.route('/<int:incident_id>/comment', methods=['POST'])
@login_required
def add_comment(incident_id):
    incident = incident_service.get_incident_by_id(incident_id)
    if not incident:
        abort(404)

    form = CommentForm()
    if form.validate_on_submit():
        incident_service.add_comment(incident, form.comment.data, current_user)
        flash('Comment posted.', 'success')
    else:
        flash('Comment cannot be empty.', 'warning')

    return redirect(url_for('incidents.detail', incident_id=incident_id))
