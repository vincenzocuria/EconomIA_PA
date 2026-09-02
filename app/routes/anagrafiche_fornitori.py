"""Gestione anagrafica fornitori / beneficiari."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.forms.anagrafica_beneficiario_form import AnagraficaBeneficiarioForm
from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
from app.routes.anagrafiche import bp
from app.services.anagrafiche_elimina import elimina_riga
from app.services.anagrafiche_sync import aggiorna_beneficiario, salva_beneficiario
from app.services.audit_log import scrivi_audit


@bp.route("/fornitori/nuovo", methods=["GET", "POST"])
@login_required
def fornitore_nuovo():
    form = AnagraficaBeneficiarioForm()
    if form.validate_on_submit():
        row = salva_beneficiario(form.denominazione.data, form.cf_piva.data)
        if row is None:
            flash("Inserisci la denominazione del fornitore.", "danger")
        else:
            db.session.flush()
            scrivi_audit(
                "anagrafica_beneficiario",
                row.id,
                "creazione",
                {"denominazione": row.denominazione},
            )
            db.session.commit()
            flash("Fornitore salvato.", "success")
            return redirect(url_for("anagrafiche.lista", tab="fornitori"))
    return render_template(
        "anagrafiche/beneficiario_modifica.html",
        form=form,
        titolo="Nuovo fornitore",
        row=None,
    )


@bp.route("/fornitori/<int:id>/modifica", methods=["GET", "POST"])
@login_required
def fornitore_modifica(id: int):
    row = AnagraficaBeneficiario.query.get_or_404(id)
    form = AnagraficaBeneficiarioForm()
    if request.method == "GET":
        form.denominazione.data = row.denominazione
        form.cf_piva.data = row.cf_piva or ""
    if form.validate_on_submit():
        err = aggiorna_beneficiario(row, form.denominazione.data, form.cf_piva.data)
        if err:
            flash(err, "danger")
        else:
            scrivi_audit("anagrafica_beneficiario", row.id, "modifica", {})
            db.session.commit()
            flash("Fornitore aggiornato.", "success")
            return redirect(url_for("anagrafiche.lista", tab="fornitori"))
    return render_template(
        "anagrafiche/beneficiario_modifica.html",
        form=form,
        titolo="Modifica fornitore",
        row=row,
    )


@bp.route("/fornitori/<int:id>/elimina", methods=["POST"])
@login_required
def fornitore_elimina(id: int):
    row = AnagraficaBeneficiario.query.get_or_404(id)
    nome = row.denominazione
    elimina_riga(row, entita="anagrafica_beneficiario", dettaglio={"denominazione": nome})
    flash("Fornitore eliminato.", "success")
    return redirect(url_for("anagrafiche.lista", tab="fornitori"))
