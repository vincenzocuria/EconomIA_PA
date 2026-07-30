"""Collega un file upload a un buono esistente."""
from datetime import date

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.config import INSTANCE_DIR
from app.extensions import db
from app.models.allegato import Allegato, TipoAllegato
from app.models.buono import BuonoEconomale
from app.services.audit_log import scrivi_audit
from app.services.upload_allegato import (
    estensione_consentita,
    mime_consentito_per_estensione,
    nome_file_allegato,
    salva_upload,
)


def allega_file_a_buono(
    b: BuonoEconomale,
    file: FileStorage,
    tipo: TipoAllegato = TipoAllegato.autorizzazione,
    *,
    is_principale: bool = True,
) -> tuple[Allegato | None, str | None]:
    if not file or not file.filename:
        return None, None
    ext = estensione_consentita(file.filename)
    if not ext:
        return None, "Formato allegato non ammesso (PDF o immagini)."
    mime = file.mimetype or ""
    if not mime_consentito_per_estensione(mime, ext):
        return None, "MIME non coerente con l'estensione del file."
    data_doc = b.data_buono or date.today()
    nome = nome_file_allegato(
        data_doc,
        "BUO",
        b.numero_progressivo,
        tipo,
        b.richiedente or b.beneficiario or "",
        str(b.importo_speso or b.importo_autorizzato),
        ext,
    )
    dest = INSTANCE_DIR / "uploads" / str(b.anno)
    path, digest = salva_upload(file, dest, nome)
    mime_finale = "image/jpeg" if path.suffix.lower() == ".jpg" else mime
    row = Allegato(
        filename_stored=str(path.relative_to(INSTANCE_DIR)),
        original_name=secure_filename(file.filename),
        mime_type=mime_finale,
        sha256=digest,
        tipo_documento=tipo,
        movimento_id=None,
        buono_id=b.id,
        anno=b.anno,
        is_principale=is_principale,
    )
    db.session.add(row)
    db.session.commit()
    scrivi_audit("allegato", row.id, "upload", {"file": nome, "da": "buono"})
    return row, None
