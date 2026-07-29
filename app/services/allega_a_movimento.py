"""Collega un file upload a un movimento esistente."""
from datetime import date

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.config import INSTANCE_DIR
from app.extensions import db
from app.models.allegato import Allegato, TipoAllegato
from app.models.movimento import Movimento
from app.services.audit_log import scrivi_audit
from app.services.giustificativo import segna_giustificato
from app.services.upload_allegato import (
    estensione_consentita,
    mime_consentito_per_estensione,
    nome_file_allegato,
    salva_upload,
)


def allega_file_a_movimento(
    m: Movimento,
    file: FileStorage,
    tipo: TipoAllegato = TipoAllegato.ricevuta,
    *,
    is_principale: bool = True,
) -> tuple[Allegato | None, str | None]:
    """
    Salva l'allegato e lo collega al movimento.
    Ritorna (allegato, None) oppure (None, messaggio_errore).
    """
    if not file or not file.filename:
        return None, None
    ext = estensione_consentita(file.filename)
    if not ext:
        return None, "Formato allegato non ammesso (PDF o immagini)."
    mime = file.mimetype or ""
    if not mime_consentito_per_estensione(mime, ext):
        return None, "MIME non coerente con l'estensione del file."
    data_doc = m.data_movimento or date.today()
    nome = nome_file_allegato(
        data_doc,
        "MOV",
        m.numero_progressivo,
        tipo,
        m.beneficiario_fornitore or "",
        str(m.importo),
        ext,
    )
    dest = INSTANCE_DIR / "uploads" / str(m.anno)
    path, digest = salva_upload(file, dest, nome)
    mime_finale = "image/jpeg" if path.suffix.lower() == ".jpg" else mime
    row = Allegato(
        filename_stored=str(path.relative_to(INSTANCE_DIR)),
        original_name=secure_filename(file.filename),
        mime_type=mime_finale,
        sha256=digest,
        tipo_documento=tipo,
        movimento_id=m.id,
        buono_id=None,
        anno=m.anno,
        is_principale=is_principale,
    )
    db.session.add(row)
    segna_giustificato(m)
    db.session.commit()
    scrivi_audit("allegato", row.id, "upload", {"file": nome, "da": "movimento"})
    return row, None
