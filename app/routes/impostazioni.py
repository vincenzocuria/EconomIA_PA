from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app.config import INSTANCE_DIR
from app.extensions import db
from app.forms.impostazioni_form import EconomoForm, EnteForm, SaldoAnnoForm
from app.models.cassetto import SaldoAnnuale
from app.models.economo import EconomoSettings
from app.models.ente import EnteSettings
from app.services.audit_log import scrivi_audit
from app.services.documenti_economo import (
    mime_documento,
    path_documento_economo,
    salva_documento_economo,
)
from app.services.logo_ente import logo_ente_path
from app.services.upload_allegato import estensione_consentita, salva_upload

bp = Blueprint("impostazioni", __name__, url_prefix="/impostazioni")

_LOGO_PREVIEW_MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


@bp.route("/ente/logo-preview")
@login_required
def logo_preview():
    path = logo_ente_path()
    if path is not None and path.suffix.lower().lstrip(".") not in _LOGO_PREVIEW_MIME:
        path = None
    if path is None:
        abort(404)
    ext = path.suffix.lower().lstrip(".")
    return send_file(path, mimetype=_LOGO_PREVIEW_MIME[ext])


@bp.route("/ente", methods=["GET", "POST"])
@login_required
def ente():
    row = EnteSettings.query.get_or_404(1)
    form = EnteForm(obj=row)
    if form.validate_on_submit():
        row.denominazione = form.denominazione.data or ""
        row.codice_fiscale_ente = form.codice_fiscale_ente.data or ""
        row.codice_istat = form.codice_istat.data or ""
        row.indirizzo = form.indirizzo.data or ""
        row.cap = form.cap.data or ""
        row.comune = form.comune.data or ""
        row.provincia = form.provincia.data or ""
        row.pec = form.pec.data or ""
        row.email = form.email.data or ""
        row.telefono = form.telefono.data or ""
        row.note_legali = form.note_legali.data or ""
        f = form.logo.data
        if f and f.filename:
            ext = estensione_consentita(f.filename)
            if ext and ext != "pdf":
                logos = INSTANCE_DIR / "logos"
                fname = secure_filename(f"logo_{date.today().year}.{ext}")
                path, _ = salva_upload(f, logos, fname)
                row.logo_path = str(path.relative_to(INSTANCE_DIR).as_posix())
        db.session.commit()
        scrivi_audit("ente", 1, "aggiornamento", {})
        flash("Dati ente salvati.", "success")
        return redirect(url_for("impostazioni.ente"))
    return render_template("impostazioni/ente.html", form=form, row=row)


@bp.route("/economo/determina")
@login_required
def economo_determina():
    path = path_documento_economo("determina_path")
    if path is None:
        abort(404)
    return send_file(path, mimetype=mime_documento(path), as_attachment=False, download_name=path.name)


@bp.route("/economo/regolamento")
@login_required
def economo_regolamento():
    path = path_documento_economo("regolamento_path")
    if path is None:
        abort(404)
    return send_file(path, mimetype=mime_documento(path), as_attachment=False, download_name=path.name)


@bp.route("/economo", methods=["GET", "POST"])
@login_required
def economo():
    row = EconomoSettings.query.get_or_404(1)
    form = EconomoForm(obj=row)
    if form.validate_on_submit():
        row.cognome = form.cognome.data or ""
        row.nome = form.nome.data or ""
        row.codice_fiscale = form.codice_fiscale.data or ""
        row.qualifica = form.qualifica.data or ""
        row.incarico_dal = form.incarico_dal.data
        row.delibera_nomina = form.delibera_nomina.data or ""
        row.telefono = form.telefono.data or ""
        row.email = form.email.data or ""
        row.note = form.note.data or ""

        rel_det = salva_documento_economo(form.determina.data, "determina")
        if rel_det:
            row.determina_path = rel_det
        rel_reg = salva_documento_economo(form.regolamento.data, "regolamento")
        if rel_reg:
            row.regolamento_path = rel_reg

        db.session.commit()
        scrivi_audit("economo", 1, "aggiornamento", {})
        flash("Dati economo salvati.", "success")
        return redirect(url_for("impostazioni.economo"))
    return render_template("impostazioni/economo.html", form=form, row=row)


@bp.route("/cassa", methods=["GET", "POST"])
@login_required
def cassa():
    anno = int(request.args.get("anno", date.today().year))
    row = SaldoAnnuale.query.get(anno)
    if row is None:
        row = SaldoAnnuale(anno=anno, saldo_iniziale=0, saldo_conto_iniziale=0)
        db.session.add(row)
        db.session.commit()
    form = SaldoAnnoForm(obj=row)
    if form.validate_on_submit():
        row.saldo_iniziale = form.saldo_iniziale.data
        row.saldo_conto_iniziale = form.saldo_conto_iniziale.data
        row.note = form.note.data or ""
        db.session.commit()
        scrivi_audit("saldo_annuale", anno, "aggiornamento", {})
        flash("Saldi iniziali cassa e conto aggiornati.", "success")
        return redirect(url_for("impostazioni.cassa", anno=anno))
    return render_template("impostazioni/cassa.html", form=form, row=row, anno=anno)
