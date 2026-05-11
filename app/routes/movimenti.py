from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.movimento_form import MovimentoForm, StornoForm
from app.models.buono import BuonoEconomale
from app.models.movimento import Movimento, StatoMovimento, TipoMovimento, trimestre_da_data
from app.services.audit_log import scrivi_audit
from app.services.progressivi import prossimo_numero_movimento

bp = Blueprint("movimenti", __name__, url_prefix="/movimenti")


def _buoni_scelte(anno: int):
    opts = [(0, "— Nessun buono —")]
    for b in BuonoEconomale.query.filter_by(anno=anno).order_by(BuonoEconomale.numero_progressivo):
        opts.append((b.id, f"{b.numero_progressivo:04d}/{b.anno} — {b.causale[:40] if b.causale else ''}"))
    return opts


def _popola_form_movimento(form: MovimentoForm, anno: int, m: Movimento | None = None):
    form.buono_id.choices = _buoni_scelte(anno)
    if m:
        form.data_movimento.data = m.data_movimento
        form.tipo.data = m.tipo.value
        form.importo.data = m.importo
        form.causale.data = m.causale
        form.beneficiario_fornitore.data = m.beneficiario_fornitore
        form.cf_piva.data = m.cf_piva
        form.buono_id.data = m.buono_id or 0
        form.num_documento_fiscale.data = m.num_documento_fiscale
        form.data_documento_fiscale.data = m.data_documento_fiscale
        form.modalita_pagamento.data = m.modalita_pagamento
        form.capitolo_riferimento.data = m.capitolo_riferimento
        form.note.data = m.note
        form.stato.data = m.stato.value


def _movimento_da_form(form: MovimentoForm, anno: int, numero: int, m: Movimento | None) -> Movimento:
    if m is None:
        m = Movimento(anno=anno, numero_progressivo=numero)
        m.created_by_id = current_user.id
    m.data_movimento = form.data_movimento.data
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
    m.capitolo_riferimento = form.capitolo_riferimento.data or ""
    m.note = form.note.data or ""
    m.stato = StatoMovimento(form.stato.data)
    m.trimestre = trimestre_da_data(m.data_movimento)
    return m


@bp.route("/")
@login_required
def lista():
    anno = int(request.args.get("anno", date.today().year))
    rows = Movimento.query.filter_by(anno=anno).order_by(Movimento.numero_progressivo.desc()).all()
    return render_template("movimenti/lista.html", rows=rows, anno=anno)


@bp.route("/nuovo", methods=["GET", "POST"])
@login_required
def nuovo():
    anno = int(request.args.get("anno", date.today().year))
    form = MovimentoForm()
    form.buono_id.choices = _buoni_scelte(anno)
    if request.method == "GET":
        form.stato.data = StatoMovimento.registrato.value
    if form.validate_on_submit():
        num = prossimo_numero_movimento(anno)
        m = _movimento_da_form(form, anno, num, None)
        db.session.add(m)
        db.session.commit()
        scrivi_audit("movimento", m.id, "creazione", {"n": num, "anno": anno})
        flash("Movimento registrato.", "success")
        return redirect(url_for("movimenti.lista", anno=anno))
    return render_template("movimenti/modifica.html", form=form, titolo="Nuovo movimento", anno=anno, m=None)


@bp.route("/<int:id>/modifica", methods=["GET", "POST"])
@login_required
def modifica(id: int):
    m = Movimento.query.get_or_404(id)
    if m.stato == StatoMovimento.stornato:
        flash("Movimento stornato: non modificabile.", "warning")
        return redirect(url_for("movimenti.lista", anno=m.anno))
    form = MovimentoForm()
    form.buono_id.choices = _buoni_scelte(m.anno)
    if request.method == "GET":
        _popola_form_movimento(form, m.anno, m)
    if form.validate_on_submit():
        prima = {
            "importo": str(m.importo),
            "tipo": m.tipo.value,
            "stato": m.stato.value,
        }
        _movimento_da_form(form, m.anno, m.numero_progressivo, m)
        db.session.commit()
        scrivi_audit("movimento", m.id, "modifica", {"prima": prima})
        flash("Movimento aggiornato.", "success")
        return redirect(url_for("movimenti.lista", anno=m.anno))
    return render_template("movimenti/modifica.html", form=form, titolo="Modifica movimento", anno=m.anno, m=m)


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
        num = prossimo_numero_movimento(orig.anno)
        st = Movimento(
            anno=orig.anno,
            numero_progressivo=num,
            data_movimento=date.today(),
            tipo=TipoMovimento.storno,
            importo=orig.importo,
            causale=f"Storno mov. {orig.numero_progressivo:04d}/{orig.anno}. {form.note.data}",
            beneficiario_fornitore=orig.beneficiario_fornitore,
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
