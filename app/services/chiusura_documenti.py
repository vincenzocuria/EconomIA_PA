"""File del fascicolo di chiusura (estratto, promemoria, stampe)."""

from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.config import INSTANCE_DIR
from app.models.chiusura_trimestre import ChiusuraTrimestre
from app.services.upload_allegato import estensione_consentita, salva_upload

_CHIAVI = {
    "estratto": ("estratto_path", "estratto_nome", "estratto_sha"),
    "promemoria": ("promemoria_path", "promemoria_nome", "promemoria_sha"),
}


def dir_chiusura(anno: int, trimestre: int) -> Path:
    return INSTANCE_DIR / "chiusure" / str(anno) / f"T{trimestre}"


def path_sicuro(rel: str | None) -> Path | None:
    testo = (rel or "").strip().replace("\\", "/")
    if not testo or ".." in Path(testo).parts or testo.startswith("/"):
        return None
    root = INSTANCE_DIR.resolve()
    path = (INSTANCE_DIR / testo).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return path


def documento_presente(row: ChiusuraTrimestre | None, chiave: str) -> bool:
    if row is None or chiave not in _CHIAVI:
        return False
    attr = _CHIAVI[chiave][0]
    return path_sicuro(getattr(row, attr, "")) is not None


def salva_documento_chiusura(
    row: ChiusuraTrimestre,
    file: FileStorage | None,
    chiave: str,
) -> str | None:
    """Salva il file sulla riga. None se non c'è file. Solleva ValueError se non valido."""
    if chiave not in _CHIAVI:
        raise ValueError("Documento non previsto.")
    if not file or not file.filename:
        return None
    ext = estensione_consentita(file.filename)
    if not ext:
        raise ValueError("Formato non ammesso (PDF o immagini).")
    nome = secure_filename(f"{chiave}.{ext}") or f"{chiave}.{ext}"
    path, digest = salva_upload(file, dir_chiusura(row.anno, row.trimestre), nome)
    rel = path.relative_to(INSTANCE_DIR).as_posix()
    path_attr, nome_attr, sha_attr = _CHIAVI[chiave]
    setattr(row, path_attr, rel)
    setattr(row, nome_attr, secure_filename(file.filename) or nome)
    setattr(row, sha_attr, digest)
    return rel


def percorso_stampa(row: ChiusuraTrimestre | None, chiave: str) -> Path | None:
    if row is None:
        return None
    attr = "prospetto_path" if chiave == "prospetto" else "giornale_path" if chiave == "giornale" else ""
    if not attr:
        return None
    return path_sicuro(getattr(row, attr, ""))
