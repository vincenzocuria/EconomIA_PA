from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, session, url_for
from flask_login import login_required

from app.config import INSTANCE_DIR
from app.services.backup_zip import esegui_backup_zip
from app.services.excel_export import (
    export_buoni_excel,
    export_movimenti_excel,
    export_riepilogo_annuale_excel,
    nome_file_export,
)
from app.models.audit import AuditLog
from app.services.incarico_periodo import data_incarico, trimestre_in_incarico, trimestri_in_incarico
from app.services.pdf_verbale import genera_verbale_trimestrale_pdf

bp = Blueprint("backup_export", __name__, url_prefix="/strumenti")


@bp.route("/")
@login_required
def index():
    anno = int(request.args.get("anno", date.today().year))
    return render_template(
        "strumenti/index.html",
        anno=anno,
        trimestri=trimestri_in_incarico(anno),
        incarico_dal=data_incarico(),
    )


@bp.route("/audit")
@login_required
def audit_list():
    rows = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template("strumenti/audit.html", rows=rows)


def _torna_indietro() -> str:
    """Ritorna al referrer solo se è questo stesso sito."""
    ref = request.referrer or ""
    parte = urlparse(ref)
    if parte.scheme in ("http", "https") and parte.netloc == request.host and parte.path.startswith("/"):
        return ref
    return url_for("main.dashboard")


@bp.route("/backup", methods=["POST"])
@login_required
def backup():
    ok, msg, path = esegui_backup_zip()
    if not ok or path is None:
        flash(msg, "danger")
        return redirect(_torna_indietro())
    session["backup_da_scaricare"] = path.name
    flash(msg, "success")
    return redirect(_torna_indietro())


@bp.route("/backup/scarica")
@login_required
def backup_scarica():
    nome = session.pop("backup_da_scaricare", None)
    if not nome or Path(nome).name != nome:
        abort(404)
    base = (INSTANCE_DIR / "backups").resolve()
    path = (base / nome).resolve()
    if base not in path.parents or not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True, download_name=path.name)


@bp.route("/export/movimenti")
@login_required
def export_movimenti():
    anno = int(request.args.get("anno", date.today().year))
    bio = export_movimenti_excel(anno)
    return send_file(
        bio,
        as_attachment=True,
        download_name=nome_file_export("movimenti", anno),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/export/buoni")
@login_required
def export_buoni():
    anno = int(request.args.get("anno", date.today().year))
    bio = export_buoni_excel(anno)
    return send_file(
        bio,
        as_attachment=True,
        download_name=nome_file_export("buoni", anno),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/export/riepilogo-annuale")
@login_required
def export_riepilogo():
    anno = int(request.args.get("anno", date.today().year))
    bio = export_riepilogo_annuale_excel(anno)
    return send_file(
        bio,
        as_attachment=True,
        download_name=nome_file_export("riepilogo_annuale", anno),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/verbale/<int:anno>/<int:trimestre>", methods=["POST"])
@login_required
def verbale_pdf(anno: int, trimestre: int):
    if trimestre < 1 or trimestre > 4 or not trimestre_in_incarico(anno, trimestre):
        flash("Trimestre precedente all'inizio dell'incarico o non valido.", "warning")
        return redirect(url_for("backup_export.index", anno=anno))
    path = genera_verbale_trimestrale_pdf(anno, trimestre)
    return send_file(path, as_attachment=True, download_name=path.name)
