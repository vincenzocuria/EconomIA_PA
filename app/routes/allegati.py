from datetime import date
from pathlib import Path

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from sqlalchemy import or_
from flask_login import login_required
from PIL import Image
from werkzeug.utils import secure_filename

from app.config import INSTANCE_DIR
from app.extensions import db
from app.forms.allegato_form import AllegatoForm
from app.models.allegato import Allegato, TipoAllegato
from app.models.buono import BuonoEconomale
from app.models.movimento import Movimento
from app.services.audit_log import scrivi_audit
from app.services.file_hash import sha256_file
from app.services.upload_allegato import (
    estensione_consentita,
    mime_consentito_per_estensione,
    nome_file_allegato,
    nome_file_estratto_conto,
    salva_upload,
)

bp = Blueprint("allegati", __name__, url_prefix="/allegati")


def _mov_scelte(anno: int):
    opts = [(0, "— Nessun movimento —")]
    for m in Movimento.query.filter_by(anno=anno).order_by(Movimento.numero_progressivo.desc()):
        opts.append((m.id, f"{m.numero_progressivo:04d}/{m.anno} — {(m.causale or '')[:35]}"))
    return opts


def _buoni_scelte(anno: int):
    opts = [(0, "— Nessun buono —")]
    for b in BuonoEconomale.query.filter_by(anno=anno).order_by(BuonoEconomale.numero_progressivo.desc()):
        opts.append((b.id, f"{b.numero_progressivo:04d}/{b.anno}"))
    return opts


@bp.route("/")
@login_required
def lista():
    anno = int(request.args.get("anno", date.today().year))
    rows = (
        Allegato.query.outerjoin(Movimento, Allegato.movimento_id == Movimento.id)
        .outerjoin(BuonoEconomale, Allegato.buono_id == BuonoEconomale.id)
        .filter(
            or_(
                Movimento.anno == anno,
                BuonoEconomale.anno == anno,
                Allegato.anno == anno,
            )
        )
        .order_by(Allegato.created_at.desc())
        .limit(200)
        .all()
    )
    form = AllegatoForm()
    form.movimento_id.choices = _mov_scelte(anno)
    form.buono_id.choices = _buoni_scelte(anno)
    return render_template("allegati/lista.html", rows=rows, anno=anno, form=form)


@bp.route("/carica", methods=["POST"])
@login_required
def carica():
    anno = int(request.form.get("anno", date.today().year))
    form = AllegatoForm()
    form.movimento_id.choices = _mov_scelte(anno)
    form.buono_id.choices = _buoni_scelte(anno)
    if not form.validate_on_submit():
        flash("Errore validazione allegato.", "danger")
        return redirect(url_for("allegati.lista", anno=anno))
    f = form.file.data
    if not f or not f.filename:
        flash("Seleziona un file.", "warning")
        return redirect(url_for("allegati.lista", anno=anno))
    ext = estensione_consentita(f.filename)
    if not ext:
        flash("Formato non ammesso.", "danger")
        return redirect(url_for("allegati.lista", anno=anno))
    mime = f.mimetype or ""
    if not mime_consentito_per_estensione(mime, ext):
        flash("MIME non coerente con l'estensione.", "danger")
        return redirect(url_for("allegati.lista", anno=anno))
    mid = form.movimento_id.data or 0
    bid = form.buono_id.data or 0
    tipo = form.tipo_documento.data
    if tipo != TipoAllegato.estratto_conto and not mid and not bid:
        flash("Collegare almeno un movimento o un buono.", "warning")
        return redirect(url_for("allegati.lista", anno=anno))
    m = Movimento.query.get(mid) if mid else None
    b = BuonoEconomale.query.get(bid) if bid else None
    data_doc = date.today()
    if m or b:
        prefisso = "MOV" if m else "BUO"
        num = m.numero_progressivo if m else b.numero_progressivo
        ben = (m.beneficiario_fornitore if m else (b.beneficiario if b else "")) or ""
        imp = str(m.importo if m else (b.importo_speso if b else 0))
        nome = nome_file_allegato(data_doc, prefisso, num, tipo, ben, imp, ext)
    else:
        nome = nome_file_estratto_conto(data_doc, anno, ext)
    dest = INSTANCE_DIR / "uploads" / str(anno)
    path, digest = salva_upload(f, dest, nome)
    if form.comprimi.data and ext in ("jpg", "jpeg", "png", "webp"):
        try:
            img = Image.open(path).convert("RGB")
            if ext in ("png", "webp"):
                nuovo = path.with_suffix(".jpg")
                img.save(nuovo, format="JPEG", quality=82, optimize=True)
                path.unlink(missing_ok=True)
                path = nuovo
            else:
                img.save(path, format="JPEG", quality=82, optimize=True)
            digest = sha256_file(path)
        except OSError:
            pass
    mime_finale = "image/jpeg" if path.suffix.lower() == ".jpg" else mime
    row = Allegato(
        filename_stored=str(path.relative_to(INSTANCE_DIR)),
        original_name=secure_filename(f.filename),
        mime_type=mime_finale,
        sha256=digest,
        tipo_documento=tipo,
        movimento_id=mid or None,
        buono_id=bid or None,
        anno=anno,
        is_principale=bool(form.is_principale.data),
    )
    db.session.add(row)
    db.session.commit()
    scrivi_audit("allegato", row.id, "upload", {"file": nome})
    flash("Allegato caricato.", "success")
    return redirect(url_for("allegati.lista", anno=anno))


@bp.route("/<int:id>/file")
@login_required
def file_(id: int):
    a = Allegato.query.get_or_404(id)
    path = INSTANCE_DIR / a.filename_stored
    if not path.is_file():
        abort(404)
    dl = request.args.get("download")
    return send_file(path, as_attachment=bool(dl), download_name=a.original_name or path.name)


@bp.route("/<int:id>/ruota", methods=["POST"])
@login_required
def ruota(id: int):
    a = Allegato.query.get_or_404(id)
    path = INSTANCE_DIR / a.filename_stored
    if not path.suffix.lower().lstrip(".") in ("jpg", "jpeg", "png", "webp"):
        flash("Rotazione disponibile solo per immagini.", "warning")
        return redirect(url_for("allegati.lista"))
    try:
        img = Image.open(path)
        img = img.rotate(-90, expand=True)
        img.save(path)
        scrivi_audit("allegato", a.id, "rotazione", {})
        flash("Immagine ruotata.", "success")
    except OSError:
        flash("Errore durante la rotazione.", "danger")
    return redirect(url_for("allegati.lista"))
