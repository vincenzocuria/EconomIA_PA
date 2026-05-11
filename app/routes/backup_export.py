from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from app.services.backup_zip import esegui_backup_zip
from app.services.excel_export import (
    export_buoni_excel,
    export_movimenti_excel,
    export_riepilogo_annuale_excel,
    nome_file_export,
)
from app.models.audit import AuditLog
from app.services.pdf_verbale import genera_verbale_trimestrale_pdf

bp = Blueprint("backup_export", __name__, url_prefix="/strumenti")


@bp.route("/")
@login_required
def index():
    anno = int(request.args.get("anno", date.today().year))
    return render_template("strumenti/index.html", anno=anno)


@bp.route("/audit")
@login_required
def audit_list():
    rows = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template("strumenti/audit.html", rows=rows)


@bp.route("/backup", methods=["POST"])
@login_required
def backup():
    ok, msg, path = esegui_backup_zip()
    if ok and path:
        flash(msg, "success")
        return send_file(path, as_attachment=True, download_name=path.name)
    flash(msg, "danger")
    return redirect(url_for("backup_export.index"))


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
    if trimestre < 1 or trimestre > 4:
        flash("Trimestre non valido.", "danger")
        return redirect(url_for("backup_export.index", anno=anno))
    path = genera_verbale_trimestrale_pdf(anno, trimestre)
    return send_file(path, as_attachment=True, download_name=path.name)
