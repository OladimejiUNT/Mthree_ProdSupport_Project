"""Main controller — landing page and health endpoint."""
from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('incidents.index'))
    return render_template('index.html')


@main_bp.route('/health')
def health():
    """Simple health-check endpoint for load balancers / uptime monitors."""
    return {'status': 'ok'}, 200
