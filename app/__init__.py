"""Flask application factory."""
import os
import click
from flask import Flask, render_template
from app.config import config
from app.extensions import db, login_manager, migrate, csrf, oauth


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    if config_name not in config:
        config_name = 'development'

    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config[config_name])

    # --- Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    oauth.init_app(app)

    # --- Prometheus metrics (auto-exposes /metrics) ---
    if not app.config.get('TESTING'):
        from prometheus_flask_exporter import PrometheusMetrics
        PrometheusMetrics(app, group_by='endpoint')

    # --- Google OAuth provider ---
    if app.config.get('GOOGLE_CLIENT_ID'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )

    # --- Blueprints ---
    from app.controllers.main import main_bp
    from app.controllers.auth import auth_bp
    from app.controllers.incidents import incidents_bp
    from app.controllers.admin import admin_bp
    from app.controllers.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(incidents_bp, url_prefix='/incidents')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Exempt the REST API from CSRF (uses session auth, stateless clients)
    csrf.exempt(api_bp)

    # --- Error handlers ---
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # --- CLI commands ---
    _register_commands(app)

    # --- DB init + seed (development convenience) ---
    with app.app_context():
        db.create_all()
        _seed_default_categories()

    return app


def _register_commands(app):
    @app.cli.command('create-admin')
    @click.option('--email', prompt='Email')
    @click.option('--name', prompt='Full name')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(email, name, password):
        """Create an admin user."""
        from app.models.user import User
        if User.query.filter_by(email=email.lower()).first():
            click.echo(f'ERROR: {email} is already registered.')
            return
        user = User(email=email.lower(), name=name, role='admin')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Admin user {email} created.')


def _seed_default_categories():
    """Seed default incident categories on first run."""
    from app.models.category import Category
    if Category.query.count() == 0:
        seeds = [
            Category(name='Application', description='Application errors and software bugs'),
            Category(name='Network', description='Network connectivity and infrastructure issues'),
            Category(name='Hardware', description='Physical hardware failures'),
            Category(name='Security', description='Security incidents and vulnerabilities'),
            Category(name='Database', description='Database errors and performance issues'),
            Category(name='Access & Permissions', description='User access management'),
            Category(name='Performance', description='System slowness and performance issues'),
            Category(name='Other', description='Miscellaneous IT issues'),
        ]
        db.session.add_all(seeds)
        db.session.commit()
