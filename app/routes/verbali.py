from datetime import date
from pathlib import Path

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app.config import INSTANCE_DIR
from app.extensions import db
from app.forms.verbale_verifica_form import VerbaleVerificaForm
from app.models.verbale_verifica import VerbaleVerifica
from app.services.audit_log import scrivi_audit
from app.services.upload_allegato import estensione_consentita, mime_consentito_per_estensione
from app.services.verbale_archivio import salva_pdf_verbale

bp = Blueprint("verbali", __name__, url_prefix="/verbali")


@bp.route("/")
@login_required
def lista():
    anno = int(request.args.get("anno", date.today().year))
    rows = (
        VerbaleVerifica.query.filter_by(anno=anno)
        .order_by(VerbaleVerifica.trimestre.desc(), VerbaleVerifica.numero.desc())
        .all()
    )
    form = VerbaleVerificaForm()
    if not form.data_verbale.data:
        form.data_verbale.data = date.today()
    if not form.oggetto.data:
        form.oggetto.data = f"VERIFICA DI CASSA ECONOMALE — TRIMESTRE {form.trimestre.data or 1} {anno}"
    return render_template("verbali/lista.html", rows=rows, anno=anno, form=form)


@bp.route("/carica", methods=["POST"])
@login_required
def carica():
    anno = int(request.form.get("anno", date.today().year))
    form = VerbaleVerificaForm()
    if not form.validate_on_submit():
        flash("Errore validazione verbale.", "danger")
        return redirect(url_for("verbali.lista", anno=anno))
    f = form.file.data
    if not f or not f.filename:
        flash("Seleziona un PDF.", "warning")
        return redirect(url_for("verbali.lista", anno=anno))
    ext = estensione_consentita(f.filename)
    if ext != "pdf":
        flash("Consentito solo PDF.", "danger")
        return redirect(url_for("verbali.lista", anno=anno))
    mime = f.mimetype or ""
    if not mime_consentito_per_estensione(mime, ext):
        flash("MIME non coerente (atteso application/pdf).", "danger")
        return redirect(url_for("verbali.lista", anno=anno))

    trim = form.trimestre.data
    esistente = VerbaleVerifica.query.filter_by(anno=anno, trimestre=trim).first()
    if esistente:
        vecchio = INSTANCE_DIR / esistente.filename_stored
        if vecchio.is_file():
            vecchio.unlink(missing_ok=True)
        db.session.delete(esistente)
        db.session.flush()

    _path, rel, digest = salva_pdf_verbale(
        f,
        form.data_verbale.data,
        anno,
        trim,
        form.numero.data,
        ext,
    )
    row = VerbaleVerifica(
        numero=form.numero.data,
        data_verbale=form.data_verbale.data,
        anno=anno,
        trimestre=trim,
        oggetto=(form.oggetto.data or "").strip(),
        note=(form.note.data or "").strip(),
        filename_stored=rel,
        original_name=secure_filename(f.filename) or Path(rel).name,
        mime_type="application/pdf",
        sha256=digest,
    )
    db.session.add(row)
    db.session.commit()
    scrivi_audit(
        "verbale_verifica",
        row.id,
        "upload",
        {"numero": row.numero, "anno": anno, "trimestre": trim},
    )
    flash(f"Verbale n. {row.numero} (T{trim}/{anno}) salvato.", "success")
    return redirect(url_for("verbali.lista", anno=anno))


@bp.route("/<int:id>/file")
@login_required
def file_(id: int):
    v = VerbaleVerifica.query.get_or_404(id)
    path = INSTANCE_DIR / v.filename_stored
    if not path.is_file():
        abort(404)
    dl = request.args.get("download")
    return send_file(
        path,
        as_attachment=bool(dl),
        download_name=v.original_name or path.name,
        mimetype=v.mime_type or "application/pdf",
    )


@bp.route("/<int:id>/elimina", methods=["POST"])
@login_required
def elimina(id: int):
    v = VerbaleVerifica.query.get_or_404(id)
    anno = v.anno
    path = INSTANCE_DIR / v.filename_stored
    if path.is_file():
        path.unlink(missing_ok=True)
    scrivi_audit("verbale_verifica", v.id, "eliminazione", {"numero": v.numero})
    db.session.delete(v)
    db.session.commit()
    flash("Verbale eliminato dall'archivio.", "success")
    return redirect(url_for("verbali.lista", anno=anno))
