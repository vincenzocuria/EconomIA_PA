"""Pagine della chiusura trimestre."""

from datetime import date
from pathlib import Path

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from app.extensions import db
from app.forms.chiusura_form import FascicoloChiusuraForm, QuietanzaForm, VoceContoForm
from app.models.allegato import TipoAllegato
from app.models.buono import BuonoEconomale
from app.models.chiusura_trimestre import VoceRiconciliazioneConto
from app.services.allega_a_buono import allega_file_a_buono
from app.services.audit_log import scrivi_audit
from app.services.chiusura_blocco import rifiuta_se_chiuso
from app.services.chiusura_checklist import controlla_chiusura
from app.services.chiusura_documenti import (
    dir_chiusura,
    documento_presente,
    path_sicuro,
    percorso_stampa,
    salva_documento_chiusura,
)
from app.services.chiusura_esecutiva import chiudi_trimestre, riapri_trimestre
from app.services.chiusura_mail import destinatari_chiusura, invia_notifica_chiusura
from app.services.chiusura_record import ottieni_chiusura
from app.services.incarico_periodo import data_incarico, scelte_trimestre, trimestre_in_incarico
from app.services.mail_resend import mail_attiva
from app.services.pdf_giornale_cassa import genera_giornale_cassa
from app.services.pdf_prospetto_pagamenti import genera_prospetto_pagamenti

bp = Blueprint("chiusura", __name__, url_prefix="/chiusura")


def _anno_arg() -> int:
    try:
        return int(request.args.get("anno") or request.form.get("anno") or date.today().year)
    except (TypeError, ValueError):
        return date.today().year


def _guarda_trimestre(anno: int, trimestre: int) -> bool:
    if trimestre not in (1, 2, 3, 4) or not trimestre_in_incarico(anno, trimestre):
        flash("Trimestre fuori dall'incarico.", "warning")
        return False
    return True


@bp.route("/")
@login_required
def lista():
    anno = _anno_arg()
    righe = []
    for t, _label in scelte_trimestre(anno):
        esito = controlla_chiusura(anno, t)
        righe.append(
            {
                "trimestre": t,
                "chiusa": esito["chiusa"],
                "dovuto": esito["dovuto"],
                "pronto": esito["pronto"],
                "n_mancanti": esito["n_mancanti"],
                "n_presenti": len(esito["presenti"]),
            }
        )
    return render_template(
        "chiusura/lista.html",
        anno=anno,
        righe=righe,
        incarico_dal=data_incarico(),
        mail_attiva=mail_attiva(),
    )


@bp.route("/<int:anno>/<int:trimestre>")
@login_required
def dettaglio(anno: int, trimestre: int):
    if not _guarda_trimestre(anno, trimestre):
        return redirect(url_for("chiusura.lista", anno=anno))
    esito = controlla_chiusura(anno, trimestre)
    row = esito["chiusura"]
    form = FascicoloChiusuraForm(obj=row)
    return render_template(
        "chiusura/dettaglio.html",
        anno=anno,
        trimestre=trimestre,
        esito=esito,
        row=row,
        form=form,
        voce_form=VoceContoForm(),
        quietanza_form=QuietanzaForm(),
        mail_attiva=mail_attiva(),
        destinatari=destinatari_chiusura(),
        estratto_ok=documento_presente(row, "estratto"),
        promemoria_ok=documento_presente(row, "promemoria"),
    )


@bp.route("/<int:anno>/<int:trimestre>/fascicolo", methods=["POST"])
@login_required
def salva_fascicolo(anno: int, trimestre: int):
    if not _guarda_trimestre(anno, trimestre):
        return redirect(url_for("chiusura.lista", anno=anno))
    row = ottieni_chiusura(anno, trimestre, crea=True)
    if row.stato == "chiusa":
        flash("Trimestre chiuso: il fascicolo non si modifica.", "warning")
        return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))
    form = FascicoloChiusuraForm()
    if not form.validate_on_submit():
        flash("Controlla saldi e file del fascicolo.", "danger")
        return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))
    try:
        salva_documento_chiusura(row, form.estratto.data, "estratto")
        salva_documento_chiusura(row, form.promemoria.data, "promemoria")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
        return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))
    row.saldo_estratto_iniziale = form.saldo_estratto_iniziale.data
    row.saldo_estratto_finale = form.saldo_estratto_finale.data
    row.note = form.note.data or ""
    db.session.commit()
    scrivi_audit("chiusura_trimestre", row.id, "fascicolo", {"anno": anno, "trimestre": trimestre})
    flash("Fascicolo aggiornato.", "success")
    return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))


@bp.route("/<int:anno>/<int:trimestre>/voce", methods=["POST"])
@login_required
def aggiungi_voce(anno: int, trimestre: int):
    if not _guarda_trimestre(anno, trimestre):
        return redirect(url_for("chiusura.lista", anno=anno))
    row = ottieni_chiusura(anno, trimestre, crea=True)
    if row.stato == "chiusa":
        flash("Trimestre chiuso: le voci estratto non si modificano.", "warning")
        return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))
    form = VoceContoForm()
    if not form.validate_on_submit():
        flash("Indica descrizione e importo della voce estratto.", "danger")
        return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))
    voce = VoceRiconciliazioneConto(
        chiusura_id=row.id,
        data_voce=form.data_voce.data,
        descrizione=(form.descrizione.data or "").strip(),
        importo=form.importo.data,
    )
    db.session.add(voce)
    db.session.commit()
    flash("Voce estratto aggiunta.", "success")
    return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))


@bp.route("/<int:anno>/<int:trimestre>/voce/<int:voce_id>/elimina", methods=["POST"])
@login_required
def elimina_voce(anno: int, trimestre: int, voce_id: int):
    if not _guarda_trimestre(anno, trimestre):
        return redirect(url_for("chiusura.lista", anno=anno))
    row = ottieni_chiusura(anno, trimestre, crea=False)
    if row is None or row.stato == "chiusa":
        flash("Voce non modificabile.", "warning")
        return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))
    voce = VoceRiconciliazioneConto.query.filter_by(id=voce_id, chiusura_id=row.id).first()
    if voce is None:
        abort(404)
    db.session.delete(voce)
    db.session.commit()
    flash("Voce estratto eliminata.", "success")
    return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))


@bp.route("/<int:anno>/<int:trimestre>/quietanza/<int:buono_id>", methods=["POST"])
@login_required
def carica_quietanza(anno: int, trimestre: int, buono_id: int):
    if not _guarda_trimestre(anno, trimestre):
        return redirect(url_for("chiusura.lista", anno=anno))
    b = BuonoEconomale.query.get_or_404(buono_id)
    if rifiuta_se_chiuso(b.anno, b.data_buono):
        return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))
    form = QuietanzaForm()
    if not form.validate_on_submit():
        flash("Seleziona la quietanza firmata (PDF o immagine).", "warning")
        return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))
    _row, err = allega_file_a_buono(b, form.file.data, TipoAllegato.ricevuta, is_principale=False)
    if err or _row is None:
        flash(err or "Seleziona la quietanza firmata (PDF o immagine).", "warning")
    else:
        flash(f"Quietanza allegata al buono {b.numero_progressivo}.", "success")
    return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))


@bp.route("/<int:anno>/<int:trimestre>/chiudi", methods=["POST"])
@login_required
def chiudi(anno: int, trimestre: int):
    if not _guarda_trimestre(anno, trimestre):
        return redirect(url_for("chiusura.lista", anno=anno))
    ok, msg = chiudi_trimestre(anno, trimestre)
    flash(msg, "success" if ok else "warning")
    return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))


@bp.route("/<int:anno>/<int:trimestre>/riapri", methods=["POST"])
@login_required
def riapri(anno: int, trimestre: int):
    if not _guarda_trimestre(anno, trimestre):
        return redirect(url_for("chiusura.lista", anno=anno))
    ok, msg = riapri_trimestre(anno, trimestre)
    flash(msg, "success" if ok else "warning")
    return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))


@bp.route("/<int:anno>/<int:trimestre>/notifica", methods=["POST"])
@login_required
def notifica(anno: int, trimestre: int):
    if not _guarda_trimestre(anno, trimestre):
        return redirect(url_for("chiusura.lista", anno=anno))
    esito = controlla_chiusura(anno, trimestre)
    ok, msg = invia_notifica_chiusura(anno, trimestre, chiusa=esito["chiusa"])
    flash(msg, "success" if ok else "warning")
    return redirect(url_for("chiusura.dettaglio", anno=anno, trimestre=trimestre))


def _invia_pdf(path: Path, nome: str):
    return send_file(path, as_attachment=True, download_name=nome, mimetype="application/pdf")


@bp.route("/<int:anno>/<int:trimestre>/prospetto")
@login_required
def prospetto(anno: int, trimestre: int):
    if trimestre not in (1, 2, 3, 4):
        abort(404)
    row = ottieni_chiusura(anno, trimestre, crea=False)
    if row is not None and row.stato == "chiusa":
        salvato = percorso_stampa(row, "prospetto")
        if salvato is not None:
            return _invia_pdf(salvato, salvato.name)
    path = genera_prospetto_pagamenti(
        anno,
        trimestre,
        dir_chiusura(anno, trimestre) / f"prospetto_pagamenti_{anno}_T{trimestre}.pdf",
    )
    return _invia_pdf(path, path.name)


@bp.route("/<int:anno>/<int:trimestre>/giornale")
@login_required
def giornale(anno: int, trimestre: int):
    if trimestre not in (1, 2, 3, 4):
        abort(404)
    row = ottieni_chiusura(anno, trimestre, crea=False)
    if row is not None and row.stato == "chiusa":
        salvato = percorso_stampa(row, "giornale")
        if salvato is not None:
            return _invia_pdf(salvato, salvato.name)
    path = genera_giornale_cassa(
        anno,
        trimestre,
        dir_chiusura(anno, trimestre) / f"giornale_cassa_{anno}_T{trimestre}.pdf",
    )
    return _invia_pdf(path, path.name)


@bp.route("/<int:anno>/<int:trimestre>/file/<chiave>")
@login_required
def file_fascicolo(anno: int, trimestre: int, chiave: str):
    if chiave not in ("estratto", "promemoria"):
        abort(404)
    row = ottieni_chiusura(anno, trimestre, crea=False)
    if row is None:
        abort(404)
    rel = row.estratto_path if chiave == "estratto" else row.promemoria_path
    path = path_sicuro(rel)
    if path is None:
        abort(404)
    nome = row.estratto_nome if chiave == "estratto" else row.promemoria_nome
    return send_file(path, as_attachment=False, download_name=nome or path.name)
