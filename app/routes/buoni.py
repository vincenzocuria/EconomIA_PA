from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from app.extensions import db
from app.forms.buono_form import BuonoForm
from app.models.buono import BuonoEconomale, StatoBuono
from app.services.audit_log import scrivi_audit
from app.services.pdf_buono import genera_pdf_buono
from app.services.progressivi import prossimo_numero_buono

bp = Blueprint("buoni", __name__, url_prefix="/buoni")


def _popola_buono(form: BuonoForm, b: BuonoEconomale | None):
    if b is None:
        return
    form.data_buono.data = b.data_buono
    form.richiedente.data = b.richiedente
    form.ufficio_richiedente.data = b.ufficio_richiedente
    form.causale.data = b.causale
    form.importo_autorizzato.data = b.importo_autorizzato
    form.importo_speso.data = b.importo_speso
    form.beneficiario.data = b.beneficiario
    form.stato.data = b.stato.value
    form.note.data = b.note


def _buono_da_form(form: BuonoForm, anno: int, num: int, b: BuonoEconomale | None) -> BuonoEconomale:
    if b is None:
        b = BuonoEconomale(anno=anno, numero_progressivo=num)
    b.data_buono = form.data_buono.data
    b.richiedente = form.richiedente.data or ""
    b.ufficio_richiedente = form.ufficio_richiedente.data or ""
    b.causale = form.causale.data or ""
    b.importo_autorizzato = form.importo_autorizzato.data
    if form.importo_speso.data is not None:
        b.importo_speso = form.importo_speso.data
    elif b is None:
        b.importo_speso = 0
    b.beneficiario = form.beneficiario.data or ""
    b.stato = StatoBuono(form.stato.data)
    b.note = form.note.data or ""
    return b


@bp.route("/")
@login_required
def lista():
    anno = int(request.args.get("anno", date.today().year))
    rows = BuonoEconomale.query.filter_by(anno=anno).order_by(BuonoEconomale.numero_progressivo.desc()).all()
    return render_template("buoni/lista.html", rows=rows, anno=anno)


@bp.route("/nuovo", methods=["GET", "POST"])
@login_required
def nuovo():
    anno = int(request.args.get("anno", date.today().year))
    form = BuonoForm()
    if request.method == "GET":
        form.stato.data = StatoBuono.bozza.value
        form.data_buono.data = date.today()
        form.importo_speso.data = 0
    if form.validate_on_submit():
        num = prossimo_numero_buono(anno)
        b = _buono_da_form(form, anno, num, None)
        db.session.add(b)
        db.session.commit()
        scrivi_audit("buono", b.id, "creazione", {"n": num, "anno": anno})
        flash("Buono creato.", "success")
        return redirect(url_for("buoni.lista", anno=anno))
    return render_template("buoni/modifica.html", form=form, titolo="Nuovo buono", anno=anno, b=None)


@bp.route("/<int:id>/modifica", methods=["GET", "POST"])
@login_required
def modifica(id: int):
    b = BuonoEconomale.query.get_or_404(id)
    form = BuonoForm()
    if request.method == "GET":
        _popola_buono(form, b)
    if form.validate_on_submit():
        _buono_da_form(form, b.anno, b.numero_progressivo, b)
        db.session.commit()
        scrivi_audit("buono", b.id, "modifica", {})
        flash("Buono aggiornato.", "success")
        return redirect(url_for("buoni.lista", anno=b.anno))
    return render_template("buoni/modifica.html", form=form, titolo="Modifica buono", anno=b.anno, b=b)


@bp.route("/<int:id>/pdf")
@login_required
def pdf(id: int):
    b = BuonoEconomale.query.get_or_404(id)
    path = genera_pdf_buono(b)
    return send_file(path, as_attachment=True, download_name=path.name)


@bp.route("/<int:id>/chiudi", methods=["POST"])
@login_required
def chiudi(id: int):
    b = BuonoEconomale.query.get_or_404(id)
    b.stato = StatoBuono.chiuso
    db.session.commit()
    scrivi_audit("buono", b.id, "chiusura", {})
    flash("Buono chiuso.", "success")
    return redirect(url_for("buoni.lista", anno=b.anno))
