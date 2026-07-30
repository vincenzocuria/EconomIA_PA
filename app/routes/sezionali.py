from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.forms.sezionale_form import SezionaleForm
from app.models.sezionale import Sezionale
from app.services.audit_log import scrivi_audit

bp = Blueprint("sezionali", __name__, url_prefix="/sezionali")


@bp.route("/")
@login_required
def lista():
    rows = Sezionale.query.order_by(Sezionale.ordinamento, Sezionale.codice).all()
    return render_template("sezionali/lista.html", rows=rows)


@bp.route("/nuovo", methods=["GET", "POST"])
@login_required
def nuovo():
    form = SezionaleForm()
    if request.method == "GET":
        form.attiva.data = True
        form.ordinamento.data = 0
    if form.validate_on_submit():
        codice = (form.codice.data or "").strip().upper()
        if Sezionale.query.filter_by(codice=codice).first():
            flash("Codice sezionale già esistente.", "danger")
        else:
            s = Sezionale(
                codice=codice,
                descrizione=(form.descrizione.data or "").strip(),
                attiva=bool(form.attiva.data),
                ordinamento=int(form.ordinamento.data or 0),
            )
            db.session.add(s)
            db.session.commit()
            scrivi_audit("sezionale", s.id, "creazione", {"codice": s.codice})
            flash("Sezionale creato.", "success")
            return redirect(url_for("sezionali.lista"))
    return render_template("sezionali/modifica.html", form=form, titolo="Nuovo sezionale", s=None)


@bp.route("/<int:id>/modifica", methods=["GET", "POST"])
@login_required
def modifica(id: int):
    s = Sezionale.query.get_or_404(id)
    form = SezionaleForm()
    if request.method == "GET":
        form.codice.data = s.codice
        form.descrizione.data = s.descrizione or ""
        form.attiva.data = s.attiva
        form.ordinamento.data = s.ordinamento
    if form.validate_on_submit():
        codice = (form.codice.data or "").strip().upper()
        altro = Sezionale.query.filter(Sezionale.codice == codice, Sezionale.id != s.id).first()
        if altro:
            flash("Codice sezionale già esistente.", "danger")
        else:
            s.codice = codice
            s.descrizione = (form.descrizione.data or "").strip()
            s.attiva = bool(form.attiva.data)
            s.ordinamento = int(form.ordinamento.data or 0)
            db.session.commit()
            scrivi_audit("sezionale", s.id, "modifica", {})
            flash("Sezionale aggiornato.", "success")
            return redirect(url_for("sezionali.lista"))
    return render_template("sezionali/modifica.html", form=form, titolo="Modifica sezionale", s=s)
