from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.forms.filiale_banca_form import FilialeBancaForm
from app.models.filiale_banca import FilialeBanca
from app.services.audit_log import scrivi_audit

bp = Blueprint("filiali_banca", __name__, url_prefix="/filiali-banca")


@bp.route("/")
@login_required
def lista():
    rows = FilialeBanca.query.order_by(FilialeBanca.ordinamento, FilialeBanca.denominazione).all()
    return render_template("filiali_banca/lista.html", rows=rows)


@bp.route("/nuovo", methods=["GET", "POST"])
@login_required
def nuovo():
    form = FilialeBancaForm()
    if request.method == "GET":
        form.attiva.data = True
        form.ordinamento.data = 0
    if form.validate_on_submit():
        f = FilialeBanca(
            denominazione=(form.denominazione.data or "").strip(),
            indirizzo=(form.indirizzo.data or "").strip(),
            attiva=bool(form.attiva.data),
            ordinamento=int(form.ordinamento.data or 0),
        )
        db.session.add(f)
        db.session.commit()
        scrivi_audit("filiale_banca", f.id, "creazione", {"denominazione": f.denominazione})
        flash("Filiale registrata.", "success")
        return redirect(url_for("filiali_banca.lista"))
    return render_template("filiali_banca/modifica.html", form=form, titolo="Nuova filiale", f=None)


@bp.route("/<int:id>/modifica", methods=["GET", "POST"])
@login_required
def modifica(id: int):
    f = FilialeBanca.query.get_or_404(id)
    form = FilialeBancaForm()
    if request.method == "GET":
        form.denominazione.data = f.denominazione
        form.indirizzo.data = f.indirizzo or ""
        form.attiva.data = f.attiva
        form.ordinamento.data = f.ordinamento
    if form.validate_on_submit():
        f.denominazione = (form.denominazione.data or "").strip()
        f.indirizzo = (form.indirizzo.data or "").strip()
        f.attiva = bool(form.attiva.data)
        f.ordinamento = int(form.ordinamento.data or 0)
        db.session.commit()
        scrivi_audit("filiale_banca", f.id, "modifica", {})
        flash("Filiale aggiornata.", "success")
        return redirect(url_for("filiali_banca.lista"))
    return render_template("filiali_banca/modifica.html", form=form, titolo="Modifica filiale", f=f)
