from flask import Blueprint, current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from app.debug_log import dlog
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
    if request.method == "GET":
        dlog(current_app, "auth.login GET next=%r", request.args.get("next"))
    if form.validate_on_submit():
        raw_u = form.username.data.strip() if form.username.data else ""
        pwd_ok_len = bool(form.password.data)
        dlog(
            current_app,
            "auth.login POST validato username=%r password_non_vuota=%s remember=%s",
            raw_u,
            pwd_ok_len,
            form.remember.data,
        )
        user = User.query.filter_by(username=raw_u).first()
        if user and user.is_active and check_password_hash(user.password_hash, form.password.data):
            dlog(current_app, "auth.login OK user_id=%s", user.id)
            login_user(user, remember=form.remember.data)
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("main.dashboard"))
        dlog(
            current_app,
            "auth.login credenziali errate username=%r utente_trovato=%s is_active=%s",
            raw_u,
            user is not None,
            bool(user and user.is_active),
        )
        if user is None:
            dlog(
                current_app,
                "auth.login: nessun record users.username=%r — se il DB è vecchio, "
                "allinea con ECONOMIA_PA_ADMIN_SYNC=1 nel .env (una volta) oppure usa lo username già in DB.",
                raw_u,
            )
        flash("Credenziali non valide.", "danger")
    elif form.is_submitted() and current_app.debug:
        dlog(current_app, "auth.login POST non validato campi=%s", list(form.errors.keys()))
    return _login_page_no_cache(render_template("auth/login.html", form=form))


@bp.route("/logout")
@login_required
def logout():
    dlog(current_app, "auth.logout user_id=%s", getattr(current_user, "id", None))
    logout_user()
    flash("Sessione chiusa.", "info")
    return redirect(url_for("auth.login"))
