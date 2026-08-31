"""Authentication controller — local login, registration, logout, Google OAuth."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required

from app.extensions import db, oauth
from app.models.user import User
from app.forms.auth_forms import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__)


# ── Local login ────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('incidents.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Contact an administrator.', 'danger')
                return render_template('auth/login.html', form=form)
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page or url_for('incidents.index'))
        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)


# ── Registration ───────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('incidents.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash('That email is already registered.', 'danger')
            return render_template('auth/register.html', form=form)

        user = User(email=email, name=form.name.data.strip(), role='user')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created — please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


# ── Logout ─────────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ── Google OAuth 2.0 ───────────────────────────────────────────────────────────

@auth_bp.route('/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            flash('Could not retrieve your Google profile. Please try again.', 'danger')
            return redirect(url_for('auth.login'))

        email = user_info.get('email', '').strip().lower()
        google_id = user_info.get('sub')
        name = user_info.get('name') or email.split('@')[0]

        # Try to find existing account by OAuth ID, then by email
        user = User.query.filter_by(oauth_provider='google', oauth_id=google_id).first()
        if not user:
            user = User.query.filter_by(email=email).first()
            if user:
                # Link the Google account to an existing local account
                user.oauth_provider = 'google'
                user.oauth_id = google_id
            else:
                user = User(
                    email=email,
                    name=name,
                    role='user',
                    oauth_provider='google',
                    oauth_id=google_id,
                )
            db.session.add(user)
            db.session.commit()

        if not user.is_active:
            flash('Your account has been deactivated.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=True)
        flash(f'Welcome, {user.name}!', 'success')
        return redirect(url_for('incidents.index'))

    except Exception:
        flash('Google authentication failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
