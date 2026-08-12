import json
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.movimento_form import MovimentoForm, StornoForm
from app.models.allegato import Allegato, TipoAllegato
from app.models.buono import BuonoEconomale
from app.models.filiale_banca import FilialeBanca
from app.models.movimento import Movimento, StatoMovimento, TipoMovimento, trimestre_da_data
from app.models.sezionale import Sezionale
from app.services.allega_a_movimento import allega_file_a_movimento
from app.services.anagrafiche_sync import sync_da_movimento
from app.services.audit_log import scrivi_audit
from app.services.filiali_scelte import scelte_filiale_per_movimento
from app.services.giustificativo import segna_giustificato
from app.services.movimento_tipi import scelte_tipo_movimento
from app.services.numero_display import formato_numero_sezionale
from app.services.movimenti_senza_allegato import query_senza_allegato
from app.services.progressivi import numero_movimento_libero, prossimo_numero_movimento
from app.services.sezionali_scelte import (
    scelte_sezionale,
    sezionale_default_per_tipo,
    sezionale_per_codice,
)

bp = Blueprint("movimenti", __name__, url_prefix="/movimenti")

TIPI_BANCA = (TipoMovimento.prelievo_banca, TipoMovimento.versamento_banca)


def _tipo_allegato_per_movimento(tipo: TipoMovimento) -> TipoAllegato:
    if tipo in TIPI_BANCA:
        return TipoAllegato.ricevuta
    if tipo == TipoMovimento.uscita:
        return TipoAllegato.scontrino
    return TipoAllegato.altro


def _salva_allegato_da_form(form: MovimentoForm, m: Movimento) -> None:
    f = form.allegato_ricevuta.data
    if not f or not getattr(f, "filename", None):
        return
    _, err = allega_file_a_movimento(m, f, _tipo_allegato_per_movimento(m.tipo))
    if err:
        flash(err, "warning")
    else:
        flash("Allegato collegato al movimento.", "success")


def _allegati_di(m: Movimento):
    return Allegato.query.filter_by(movimento_id=m.id).order_by(Allegato.created_at.desc()).all()


def _buoni_scelte(anno: int):
    from app.services.numero_display import formato_numero_sezionale

    opts = [(0, "— Nessun buono —")]
    for b in BuonoEconomale.query.filter_by(anno=anno).order_by(BuonoEconomale.numero_progressivo):
        caus = (b.causale[:40] if b.causale else "")
        opts.append((b.id, f"{formato_numero_sezionale(b)} — {caus}"))
    return opts


def _defaults_sezionale_json() -> str:
    mapping = {}
    for t in TipoMovimento:
        s = sezionale_default_per_tipo(t)
        if s:
            mapping[t.value] = s.id
    return json.dumps(mapping)


def _popola_form_movimento(form: MovimentoForm, anno: int, m: Movimento | None = None):
    form.buono_id.choices = _buoni_scelte(anno)
    form.filiale_id.choices = scelte_filiale_per_movimento(m)
    form.sezionale_id.choices = scelte_sezionale(m.sezionale_id if m else None)
    if m:
        form.sezionale_id.data = m.sezionale_id or 0
        form.numero_progressivo.data = m.numero_progressivo
        form.data_movimento.data = m.data_movimento
        form.ora_movimento.data = m.ora_movimento
        form.tipo.data = m.tipo.value
        form.importo.data = m.importo
        form.causale.data = m.causale
        form.beneficiario_fornitore.data = m.beneficiario_fornitore
        form.cf_piva.data = m.cf_piva
        form.buono_id.data = m.buono_id or 0
        form.num_documento_fiscale.data = m.num_documento_fiscale
        form.data_documento_fiscale.data = m.data_documento_fiscale
        form.modalita_pagamento.data = m.modalita_pagamento
        form.filiale_id.data = m.filiale_id or 0
        form.rif_ricevuta.data = m.rif_ricevuta or ""
        form.capitolo_riferimento.data = m.capitolo_riferimento
        form.note.data = m.note
        form.da_giustificare.data = bool(m.da_giustificare)
        form.stato.data = m.stato.value


def _azzera_campi_banca_se_serve(m: Movimento) -> None:
    if m.tipo not in TIPI_BANCA:
        m.filiale_id = None
        m.rif_ricevuta = ""


def _movimento_da_form(
    form: MovimentoForm,
    anno: int,
    numero: int,
    sezionale_id: int,
    m: Movimento | None,
) -> Movimento:
    if m is None:
        m = Movimento(anno=anno, numero_progressivo=numero, sezionale_id=sezionale_id)
        m.created_by_id = current_user.id
    else:
        m.numero_progressivo = numero
        m.sezionale_id = sezionale_id
    m.data_movimento = form.data_movimento.data
    m.ora_movimento = form.ora_movimento.data
    m.tipo = TipoMovimento(form.tipo.data)
    m.importo = form.importo.data
    m.causale = form.causale.data or ""
    m.beneficiario_fornitore = form.beneficiario_fornitore.data or ""
    m.cf_piva = form.cf_piva.data or ""
    bid = form.buono_id.data
    m.buono_id = bid if bid else None
    m.num_documento_fiscale = form.num_documento_fiscale.data or ""
    m.data_documento_fiscale = form.data_documento_fiscale.data
    m.modalita_pagamento = form.modalita_pagamento.data or ""
    fid = form.filiale_id.data
    m.filiale_id = fid if fid else None
    if m.filiale_id:
        m.filiale_banca = ""
    m.rif_ricevuta = form.rif_ricevuta.data or ""
    m.capitolo_riferimento = form.capitolo_riferimento.data or ""
    m.note = form.note.data or ""
    m.da_giustificare = bool(form.da_giustificare.data)
    m.stato = StatoMovimento(form.stato.data)
    m.trimestre = trimestre_da_data(m.data_movimento)
    _azzera_campi_banca_se_serve(m)
    sync_da_movimento(m.beneficiario_fornitore, m.cf_piva)
    return m


def _ctx_form(anno: int, m: Movimento | None = None) -> dict:
    return {
        "anno": anno,
        "m": m,
        "sezionali_default_json": _defaults_sezionale_json(),
        "prossimo_url": url_for("progressivi_api.prossimo_movimento"),
        "ac_beneficiari_url": url_for("anagrafiche_api.beneficiari"),
        "is_nuovo": m is None,
    }


@bp.route("/")
@login_required
def lista():
    anno = int(request.args.get("anno", date.today().year))
    filtro_da_giustificare = request.args.get("da_giustificare") == "1"
    filtro_senza_allegato = request.args.get("senza_allegato") == "1"
    if filtro_senza_allegato:
        q = query_senza_allegato(anno)
    else:
        q = Movimento.query.filter_by(anno=anno)
        if filtro_da_giustificare:
            q = q.filter_by(da_giustificare=True)
        q = q.order_by(Movimento.numero_progressivo.desc())
    rows = q.all()
    return render_template(
        "movimenti/lista.html",
        rows=rows,
        anno=anno,
        filtro_da_giustificare=filtro_da_giustificare and not filtro_senza_allegato,
        filtro_senza_allegato=filtro_senza_allegato,
    )


@bp.route("/<int:id>")
@login_required
def dettaglio(id: int):
    m = Movimento.query.get_or_404(id)
    return render_template(
        "movimenti/dettaglio.html",
        m=m,
        allegati=_allegati_di(m),
    )


@bp.route("/nuovo", methods=["GET", "POST"])
@login_required
def nuovo():
    anno = int(request.args.get("anno", date.today().year))
    form = MovimentoForm()
    form.tipo.choices = scelte_tipo_movimento()
    form.buono_id.choices = _buoni_scelte(anno)
    form.filiale_id.choices = scelte_filiale_per_movimento(None)
    form.sezionale_id.choices = scelte_sezionale()
    if request.method == "GET":
        form.stato.data = StatoMovimento.registrato.value
        form.data_movimento.data = date.today()
        form.tipo.data = TipoMovimento.uscita.value
        form.modalita_pagamento.data = "contanti"
        sez = sezionale_default_per_tipo(TipoMovimento.uscita)
        if sez:
            form.sezionale_id.data = sez.id
            form.numero_progressivo.data = prossimo_numero_movimento(anno, sez.id)
        sole = (
            FilialeBanca.query.filter_by(attiva=True)
            .order_by(FilialeBanca.ordinamento, FilialeBanca.denominazione)
            .all()
        )
        if len(sole) == 1:
            form.filiale_id.data = sole[0].id
    if form.validate_on_submit():
        sez_id = form.sezionale_id.data
        num = int(form.numero_progressivo.data)
        if not Sezionale.query.get(sez_id):
            flash("Sezionale non valido.", "danger")
        elif not numero_movimento_libero(anno, sez_id, num):
            flash("Numero già usato in questo sezionale/anno. Scegline un altro.", "danger")
        else:
            m = _movimento_da_form(form, anno, num, sez_id, None)
            db.session.add(m)
            db.session.commit()
            scrivi_audit(
                "movimento",
                m.id,
                "creazione",
                {"n": num, "anno": anno, "sezionale_id": sez_id},
            )
            _salva_allegato_da_form(form, m)
            flash("Movimento registrato.", "success")
            if m.tipo == TipoMovimento.uscita and not m.buono_id:
                return redirect(url_for("movimenti.proposta_buono", id=m.id))
            return redirect(url_for("movimenti.dettaglio", id=m.id))
    return render_template(
        "movimenti/modifica.html",
        form=form,
        titolo="Nuovo movimento",
        allegati=None,
        **_ctx_form(anno),
    )


@bp.route("/<int:id>/proposta-buono")
@login_required
def proposta_buono(id: int):
    m = Movimento.query.get_or_404(id)
    if m.tipo != TipoMovimento.uscita:
        return redirect(url_for("movimenti.dettaglio", id=m.id))
    if m.buono_id:
        flash("Questo movimento ha già un buono collegato.", "info")
        return redirect(url_for("movimenti.dettaglio", id=m.id))
    return render_template("movimenti/proposta_buono.html", m=m)


@bp.route("/<int:id>/modifica", methods=["GET", "POST"])
@login_required
def modifica(id: int):
    m = Movimento.query.get_or_404(id)
    if m.stato == StatoMovimento.stornato:
        flash("Movimento stornato: non modificabile.", "warning")
        return redirect(url_for("movimenti.lista", anno=m.anno))
    form = MovimentoForm()
    form.tipo.choices = scelte_tipo_movimento()
    form.buono_id.choices = _buoni_scelte(m.anno)
    form.filiale_id.choices = scelte_filiale_per_movimento(m)
    form.sezionale_id.choices = scelte_sezionale(m.sezionale_id)
    if request.method == "GET":
        _popola_form_movimento(form, m.anno, m)
    if form.validate_on_submit():
        sez_id = form.sezionale_id.data
        num = int(form.numero_progressivo.data)
        if not Sezionale.query.get(sez_id):
            flash("Sezionale non valido.", "danger")
        elif not numero_movimento_libero(m.anno, sez_id, num, escludi_id=m.id):
            flash("Numero già usato in questo sezionale/anno. Scegline un altro.", "danger")
        else:
            prima = {
                "importo": str(m.importo),
                "tipo": m.tipo.value,
                "stato": m.stato.value,
                "numero": m.numero_progressivo,
            }
            _movimento_da_form(form, m.anno, num, sez_id, m)
            db.session.commit()
            scrivi_audit("movimento", m.id, "modifica", {"prima": prima})
            _salva_allegato_da_form(form, m)
            flash("Movimento aggiornato.", "success")
            return redirect(url_for("movimenti.dettaglio", id=m.id))
    return render_template(
        "movimenti/modifica.html",
        form=form,
        titolo="Modifica movimento",
        allegati=_allegati_di(m),
        **_ctx_form(m.anno, m),
    )


@bp.route("/<int:id>/giustifica", methods=["POST"])
@login_required
def giustifica(id: int):
    m = Movimento.query.get_or_404(id)
    if m.stato == StatoMovimento.stornato:
        flash("Movimento stornato: non modificabile.", "warning")
        return redirect(url_for("movimenti.lista", anno=m.anno))
    if segna_giustificato(m):
        db.session.commit()
        scrivi_audit("movimento", m.id, "giustificato", {})
        flash("Movimento segnato come giustificato.", "success")
    else:
        flash("Il movimento non era da giustificare.", "info")
    return redirect(url_for("movimenti.modifica", id=m.id))


@bp.route("/<int:id>/storno", methods=["GET", "POST"])
@login_required
def storno(id: int):
    orig = Movimento.query.get_or_404(id)
    if orig.stato == StatoMovimento.stornato:
        flash("Movimento già stornato.", "warning")
        return redirect(url_for("movimenti.lista", anno=orig.anno))
    form = StornoForm()
    if form.validate_on_submit():
        orig.stato = StatoMovimento.stornato
        sez_id = orig.sezionale_id
        if sez_id is None:
            gen = sezionale_per_codice("GEN")
            sez_id = gen.id if gen else None
        num = prossimo_numero_movimento(orig.anno, sez_id)
        st = Movimento(
            anno=orig.anno,
            sezionale_id=sez_id,
            numero_progressivo=num,
            data_movimento=date.today(),
            tipo=TipoMovimento.storno,
            importo=orig.importo,
            causale=f"Storno mov. {formato_numero_sezionale(orig)}. {form.note.data}",
            beneficiario_fornitore=orig.beneficiario_fornitore,
            filiale_id=orig.filiale_id,
            filiale_banca=orig.filiale_banca or "",
            stato=StatoMovimento.registrato,
            trimestre=trimestre_da_data(date.today()),
            movimento_collegato_id=orig.id,
            created_by_id=current_user.id,
        )
        db.session.add(st)
        db.session.commit()
        scrivi_audit("movimento", st.id, "storno", {"origine": orig.id})
        flash("Storno registrato.", "success")
        return redirect(url_for("movimenti.lista", anno=orig.anno))
    return render_template("movimenti/storno.html", form=form, m=orig)
