from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from app.extensions import db
from app.forms.auth_form import LoginForm
from app.models.user import User

bp = Blueprint("auth", __name__)


def _login_page_no_cache(html: str):
    """Evita cache del form login (HTML obsoleto + sessione nuova = CSRF session token missing)."""
    r = make_response(html)
    r.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    r.headers["Pragma"] = "no-cache"
    return r


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        raw_u = form.username.data.strip() if form.username.data else ""
        user = User.query.filter_by(username=raw_u).first()
        if user and user.is_active and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("main.dashboard"))
        flash("Credenziali non valide.", "danger")
    return _login_page_no_cache(render_template("auth/login.html", form=form))


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessione chiusa.", "info")
    return redirect(url_for("auth.login"))
