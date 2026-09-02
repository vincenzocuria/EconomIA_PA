"""Gestione anagrafiche richiedenti, uffici e fornitori."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.forms.anagrafica_richiedente_form import AnagraficaRichiedenteForm
from app.forms.anagrafica_ufficio_form import AnagraficaUfficioForm
from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
from app.models.anagrafica_richiedente import AnagraficaRichiedente
from app.models.anagrafica_ufficio import AnagraficaUfficio
from app.services.anagrafiche_elimina import elimina_riga
from app.services.anagrafiche_sync import salva_richiedente, salva_ufficio
from app.services.anagrafiche_testo import (
    normalizza_chiave,
    normalizza_denominazione,
    normalizza_nome_persona,
)
from app.services.audit_log import scrivi_audit

bp = Blueprint("anagrafiche", __name__, url_prefix="/anagrafiche")


@bp.route("/")
@login_required
def lista():
    tab = (request.args.get("tab") or "richiedenti").strip()
    if tab not in ("richiedenti", "uffici", "fornitori"):
        tab = "richiedenti"
    richiedenti = AnagraficaRichiedente.query.order_by(AnagraficaRichiedente.nome).all()
    uffici = AnagraficaUfficio.query.order_by(AnagraficaUfficio.denominazione).all()
    fornitori = AnagraficaBeneficiario.query.order_by(AnagraficaBeneficiario.denominazione).all()
    return render_template(
        "anagrafiche/lista.html",
        tab=tab,
        richiedenti=richiedenti,
        uffici=uffici,
        fornitori=fornitori,
    )


@bp.route("/richiedenti/nuovo", methods=["GET", "POST"])
@login_required
def richiedente_nuovo():
    form = AnagraficaRichiedenteForm()
    if form.validate_on_submit():
        row = salva_richiedente(form.nome.data, form.ufficio_default.data)
        db.session.commit()
        scrivi_audit("anagrafica_richiedente", row.id, "creazione", {"nome": row.nome})
        flash("Richiedente salvato.", "success")
        return redirect(url_for("anagrafiche.lista", tab="richiedenti"))
    return render_template(
        "anagrafiche/richiedente_modifica.html",
        form=form,
        titolo="Nuovo richiedente",
        row=None,
    )


@bp.route("/richiedenti/<int:id>/modifica", methods=["GET", "POST"])
@login_required
def richiedente_modifica(id: int):
    row = AnagraficaRichiedente.query.get_or_404(id)
    form = AnagraficaRichiedenteForm()
    if request.method == "GET":
        form.nome.data = row.nome
        form.ufficio_default.data = row.ufficio_default or ""
    if form.validate_on_submit():
        nome = normalizza_nome_persona(form.nome.data)
        chiave = normalizza_chiave(nome)
        altro = AnagraficaRichiedente.query.filter(
            AnagraficaRichiedente.nome_norm == chiave,
            AnagraficaRichiedente.id != row.id,
        ).first()
        if altro:
            flash("Esiste già un richiedente con questo nome.", "danger")
        else:
            uff = normalizza_denominazione(form.ufficio_default.data)
            row.nome = nome
            row.nome_norm = chiave
            row.ufficio_default = uff
            if uff:
                salva_ufficio(uff)
            db.session.commit()
            scrivi_audit("anagrafica_richiedente", row.id, "modifica", {})
            flash("Richiedente aggiornato.", "success")
            return redirect(url_for("anagrafiche.lista", tab="richiedenti"))
    return render_template(
        "anagrafiche/richiedente_modifica.html",
        form=form,
        titolo="Modifica richiedente",
        row=row,
    )


@bp.route("/richiedenti/<int:id>/elimina", methods=["POST"])
@login_required
def richiedente_elimina(id: int):
    row = AnagraficaRichiedente.query.get_or_404(id)
    nome = row.nome
    elimina_riga(row, entita="anagrafica_richiedente", dettaglio={"nome": nome})
    flash("Richiedente eliminato.", "success")
    return redirect(url_for("anagrafiche.lista", tab="richiedenti"))


@bp.route("/uffici/nuovo", methods=["GET", "POST"])
@login_required
def ufficio_nuovo():
    form = AnagraficaUfficioForm()
    if form.validate_on_submit():
        row = salva_ufficio(form.denominazione.data, form.responsabile.data)
        db.session.commit()
        scrivi_audit("anagrafica_ufficio", row.id, "creazione", {"denominazione": row.denominazione})
        flash("Ufficio salvato.", "success")
        return redirect(url_for("anagrafiche.lista", tab="uffici"))
    return render_template(
        "anagrafiche/ufficio_modifica.html",
        form=form,
        titolo="Nuovo ufficio",
        row=None,
    )


@bp.route("/uffici/<int:id>/modifica", methods=["GET", "POST"])
@login_required
def ufficio_modifica(id: int):
    row = AnagraficaUfficio.query.get_or_404(id)
    form = AnagraficaUfficioForm()
    if request.method == "GET":
        form.denominazione.data = row.denominazione
        form.responsabile.data = row.responsabile or ""
    if form.validate_on_submit():
        nome = normalizza_denominazione(form.denominazione.data)
        chiave = normalizza_chiave(nome)
        altro = AnagraficaUfficio.query.filter(
            AnagraficaUfficio.denominazione_norm == chiave,
            AnagraficaUfficio.id != row.id,
        ).first()
        if altro:
            flash("Esiste già un ufficio con questa denominazione.", "danger")
        else:
            resp = normalizza_nome_persona(form.responsabile.data)
            row.denominazione = nome
            row.denominazione_norm = chiave
            row.responsabile = resp
            if resp:
                salva_richiedente(resp, nome)
            db.session.commit()
            scrivi_audit("anagrafica_ufficio", row.id, "modifica", {})
            flash("Ufficio aggiornato.", "success")
            return redirect(url_for("anagrafiche.lista", tab="uffici"))
    return render_template(
        "anagrafiche/ufficio_modifica.html",
        form=form,
        titolo="Modifica ufficio",
        row=row,
    )


@bp.route("/uffici/<int:id>/elimina", methods=["POST"])
@login_required
def ufficio_elimina(id: int):
    row = AnagraficaUfficio.query.get_or_404(id)
    nome = row.denominazione
    elimina_riga(row, entita="anagrafica_ufficio", dettaglio={"denominazione": nome})
    flash("Ufficio eliminato.", "success")
    return redirect(url_for("anagrafiche.lista", tab="uffici"))
