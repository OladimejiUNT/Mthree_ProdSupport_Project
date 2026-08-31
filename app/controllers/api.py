"""REST API controller — JSON endpoints for incidents (CSRF-exempt blueprint)."""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.models.category import Category
from app.services import incident_service

api_bp = Blueprint('api', __name__)


def _resp(data=None, message=None, status=200, error=None):
    body = {}
    if data is not None:
        body['data'] = data
    if message:
        body['message'] = message
    if error:
        body['error'] = error
    return jsonify(body), status


# ── Incidents ──────────────────────────────────────────────────────────────────

@api_bp.route('/incidents', methods=['GET'])
@login_required
def get_incidents():
    filters = {k: v for k, v in {
        'status': request.args.get('status'),
        'severity': request.args.get('severity'),
        'category_id': request.args.get('category_id'),
        'search': request.args.get('search'),
    }.items() if v}
    incidents = incident_service.get_all_incidents(filters)
    return _resp(data=[i.to_dict() for i in incidents])


@api_bp.route('/incidents/<int:incident_id>', methods=['GET'])
@login_required
def get_incident(incident_id):
    incident = incident_service.get_incident_by_id(incident_id)
    if not incident:
        return _resp(error='Incident not found', status=404)
    return _resp(data=incident.to_dict())


@api_bp.route('/incidents', methods=['POST'])
@login_required
def create_incident():
    data = request.get_json(silent=True) or {}
    if not data.get('title'):
        return _resp(error='title is required', status=400)
    incident = incident_service.create_incident(data, current_user, request.remote_addr)
    return _resp(data=incident.to_dict(), message='Incident created', status=201)


@api_bp.route('/incidents/<int:incident_id>', methods=['PUT'])
@login_required
def update_incident(incident_id):
    incident = incident_service.get_incident_by_id(incident_id)
    if not incident:
        return _resp(error='Incident not found', status=404)
    if incident.reported_by != current_user.id and not current_user.is_admin:
        return _resp(error='Forbidden', status=403)

    data = request.get_json(silent=True) or {}
    if not data:
        return _resp(error='No data provided', status=400)

    incident = incident_service.update_incident(incident, data, current_user, request.remote_addr)
    return _resp(data=incident.to_dict(), message='Incident updated')


@api_bp.route('/incidents/<int:incident_id>', methods=['DELETE'])
@login_required
def delete_incident(incident_id):
    incident = incident_service.get_incident_by_id(incident_id)
    if not incident:
        return _resp(error='Incident not found', status=404)
    if incident.reported_by != current_user.id and not current_user.is_admin:
        return _resp(error='Forbidden', status=403)

    incident_service.delete_incident(incident, current_user, request.remote_addr)
    return _resp(message='Incident deleted')


# ── Supporting resources ───────────────────────────────────────────────────────

@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    return _resp(data=incident_service.get_stats())


@api_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return _resp(data=[c.to_dict() for c in categories])
