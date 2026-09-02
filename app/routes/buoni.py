from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from app.extensions import db
from app.forms.buono_form import BuonoForm
from app.models.allegato import Allegato
from app.models.buono import BuonoEconomale, StatoBuono
from app.models.movimento import Movimento
from app.models.sezionale import Sezionale
from app.services.anagrafiche_sync import sync_da_buono
from app.services.audit_log import scrivi_audit
from app.services.carica_modulo_firmato import carica_modulo_firmato
from app.services.buoni_filtri import filtri_attivi, parametri_filtro, query_buoni
from app.services.buoni_kpi import kpi_buoni_anno
from app.services.buoni_senza_firma import ids_senza_firma
from app.services.buono_da_movimento import collega_movimento_a_buono, valori_precompilati_da_movimento
from app.services.docx_rimborso import genera_docx_rimborso
from app.services.pdf_buono import genera_pdf_buono
from app.services.progressivi import numero_buono_libero, prossimo_numero_buono
from app.services.redirect_interno import redirect_interno
from app.services.sezionali_scelte import scelte_sezionale, sezionale_default_buono

bp = Blueprint("buoni", __name__, url_prefix="/buoni")


def _allegati_di(b: BuonoEconomale):
    return Allegato.query.filter_by(buono_id=b.id).order_by(Allegato.created_at.desc()).all()


def _popola_buono(form: BuonoForm, b: BuonoEconomale | None):
    if b is None:
        return
    form.sezionale_id.data = b.sezionale_id or 0
    form.numero_progressivo.data = b.numero_progressivo
    form.data_buono.data = b.data_buono
    form.richiedente.data = b.richiedente
    form.ufficio_richiedente.data = b.ufficio_richiedente
    form.responsabile_ufficio.data = b.responsabile_ufficio or ""
    form.causale.data = b.causale
    form.importo_autorizzato.data = b.importo_autorizzato
    form.importo_speso.data = b.importo_speso
    form.beneficiario.data = b.beneficiario
    form.stato.data = b.stato.value
    form.note.data = b.note


def _buono_da_form(
    form: BuonoForm,
    anno: int,
    num: int,
    sezionale_id: int,
    b: BuonoEconomale | None,
) -> BuonoEconomale:
    if b is None:
        b = BuonoEconomale(anno=anno, numero_progressivo=num, sezionale_id=sezionale_id)
    else:
        b.numero_progressivo = num
        b.sezionale_id = sezionale_id
    b.data_buono = form.data_buono.data
    b.richiedente = form.richiedente.data or ""
    b.ufficio_richiedente = form.ufficio_richiedente.data or ""
    b.responsabile_ufficio = form.responsabile_ufficio.data or ""
    b.causale = form.causale.data or ""
    b.importo_autorizzato = form.importo_autorizzato.data
    if form.importo_speso.data is not None:
        b.importo_speso = form.importo_speso.data
    b.beneficiario = form.beneficiario.data or ""
    b.stato = StatoBuono(form.stato.data)
    b.note = form.note.data or ""
    sync_da_buono(
        b.richiedente,
        b.ufficio_richiedente,
        b.beneficiario,
        b.responsabile_ufficio,
    )
    return b


def _salva_firmato(form: BuonoForm, b: BuonoEconomale) -> None:
    ok, err = carica_modulo_firmato(b, form.allegato_firmato.data)
    if not ok and err is None:
        return
    if err:
        flash(err, "warning")
    else:
        flash("Modulo firmato caricato.", "success")


@bp.route("/")
@login_required
def lista():
    anno = int(request.args.get("anno", date.today().year))
    filtri = parametri_filtro(request.args)
    rows = query_buoni(anno, filtri).all()
    return render_template(
        "buoni/lista.html",
        rows=rows,
        anno=anno,
        filtri=filtri,
        filtri_on=filtri_attivi(filtri),
        kpi=kpi_buoni_anno(anno),
        senza_firma_ids=ids_senza_firma(anno),
        stati_scelte=[(e.value, e.value) for e in StatoBuono],
        sezionali_scelte=scelte_sezionale(),
    )


@bp.route("/nuovo", methods=["GET", "POST"])
@login_required
def nuovo():
    anno = int(request.args.get("anno", date.today().year))
    da_movimento_id = request.args.get("da_movimento", type=int)
    movimento = Movimento.query.get(da_movimento_id) if da_movimento_id else None
    if da_movimento_id and movimento is None:
        flash("Movimento non trovato.", "warning")
        return redirect(url_for("buoni.lista", anno=anno))
    if movimento and movimento.buono_id:
        flash("Il movimento ha già un buono collegato.", "info")
        return redirect(url_for("buoni.modifica", id=movimento.buono_id))

    form = BuonoForm()
    form.sezionale_id.choices = scelte_sezionale()
    if request.method == "GET":
        if movimento:
            vals = valori_precompilati_da_movimento(movimento)
            anno = vals["anno"]
            form.sezionale_id.data = vals["sezionale_id"]
            form.numero_progressivo.data = vals["numero_progressivo"]
            form.data_buono.data = vals["data_buono"]
            form.causale.data = vals["causale"]
            form.importo_autorizzato.data = vals["importo_autorizzato"]
            form.importo_speso.data = vals["importo_speso"]
            form.beneficiario.data = vals["beneficiario"]
            form.stato.data = vals["stato"]
        else:
            form.stato.data = StatoBuono.bozza.value
            form.data_buono.data = date.today()
            form.importo_speso.data = 0
            sez = sezionale_default_buono()
            if sez:
                form.sezionale_id.data = sez.id
                form.numero_progressivo.data = prossimo_numero_buono(anno, sez.id)

    if form.validate_on_submit():
        sez_id = form.sezionale_id.data
        num = int(form.numero_progressivo.data)
        if not Sezionale.query.get(sez_id):
            flash("Sezionale non valido.", "danger")
        elif not numero_buono_libero(anno, sez_id, num):
            flash("Numero già usato in questo sezionale/anno. Scegline un altro.", "danger")
        else:
            b = _buono_da_form(form, anno, num, sez_id, None)
            db.session.add(b)
            db.session.flush()
            if movimento:
                collega_movimento_a_buono(movimento, b)
            db.session.commit()
            scrivi_audit("buono", b.id, "creazione", {"n": num, "anno": anno, "da_movimento": da_movimento_id})
            _salva_firmato(form, b)
            flash("Buono creato. Scarica il modulo da far firmare, poi ricaricalo firmato.", "success")
            return redirect(url_for("buoni.modifica", id=b.id))

    return render_template(
        "buoni/modifica.html",
        form=form,
        titolo="Nuovo buono da movimento" if movimento else "Nuovo buono",
        anno=anno,
        b=None,
        allegati=None,
        da_movimento=movimento,
        prossimo_url=url_for("progressivi_api.prossimo_buono"),
        ac_richiedenti_url=url_for("anagrafiche_api.richiedenti"),
        ac_uffici_url=url_for("anagrafiche_api.uffici"),
        ac_beneficiari_url=url_for("anagrafiche_api.beneficiari"),
        is_nuovo=True,
    )


@bp.route("/<int:id>/modifica", methods=["GET", "POST"])
@login_required
def modifica(id: int):
    b = BuonoEconomale.query.get_or_404(id)
    form = BuonoForm()
    form.sezionale_id.choices = scelte_sezionale(b.sezionale_id)
    if request.method == "GET":
        _popola_buono(form, b)
    if form.validate_on_submit():
        sez_id = form.sezionale_id.data
        num = int(form.numero_progressivo.data)
        if not Sezionale.query.get(sez_id):
            flash("Sezionale non valido.", "danger")
        elif not numero_buono_libero(b.anno, sez_id, num, escludi_id=b.id):
            flash("Numero già usato in questo sezionale/anno. Scegline un altro.", "danger")
        else:
            _buono_da_form(form, b.anno, num, sez_id, b)
            db.session.commit()
            scrivi_audit("buono", b.id, "modifica", {})
            _salva_firmato(form, b)
            flash("Buono aggiornato.", "success")
            return redirect(url_for("buoni.modifica", id=b.id))
    return render_template(
        "buoni/modifica.html",
        form=form,
        titolo="Modifica buono",
        anno=b.anno,
        b=b,
        allegati=_allegati_di(b),
        da_movimento=None,
        prossimo_url=url_for("progressivi_api.prossimo_buono"),
        ac_richiedenti_url=url_for("anagrafiche_api.richiedenti"),
        ac_uffici_url=url_for("anagrafiche_api.uffici"),
        ac_beneficiari_url=url_for("anagrafiche_api.beneficiari"),
        is_nuovo=False,
    )


@bp.route("/<int:id>/pdf")
@login_required
def pdf(id: int):
    b = BuonoEconomale.query.get_or_404(id)
    path = genera_pdf_buono(b)
    return send_file(path, as_attachment=True, download_name=path.name)


@bp.route("/<int:id>/modulo-rimborso")
@login_required
def modulo_rimborso(id: int):
    b = BuonoEconomale.query.get_or_404(id)
    path = genera_docx_rimborso(b)
    return send_file(
        path,
        as_attachment=True,
        download_name=path.name,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@bp.route("/<int:id>/carica-firmato", methods=["POST"])
@login_required
def carica_firmato(id: int):
    b = BuonoEconomale.query.get_or_404(id)
    ok, err = carica_modulo_firmato(b, request.files.get("allegato_firmato"))
    if not ok and err is None:
        flash("Seleziona il file del modulo firmato (PDF o immagine).", "warning")
    elif err:
        flash(err, "warning")
    else:
        flash("Modulo firmato caricato.", "success")
    return redirect_interno(url_for("buoni.modifica", id=b.id))


@bp.route("/<int:id>/chiudi", methods=["POST"])
@login_required
def chiudi(id: int):
    b = BuonoEconomale.query.get_or_404(id)
    b.stato = StatoBuono.chiuso
    db.session.commit()
    scrivi_audit("buono", b.id, "chiusura", {})
    flash("Buono chiuso.", "success")
    return redirect(url_for("buoni.lista", anno=b.anno))
