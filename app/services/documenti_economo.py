"""Documenti allegati all'economo (determina, regolamento comunale)."""
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.config import INSTANCE_DIR
from app.extensions import db
from app.models.economo import EconomoSettings
from app.services.upload_allegato import estensione_consentita, salva_upload

_MIME = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def _dir_documenti() -> Path:
    return INSTANCE_DIR / "documenti_economo"


def path_documento_economo(attr: str) -> Path | None:
    row = db.session.get(EconomoSettings, 1)
    if not row:
        return None
    rel = (getattr(row, attr, None) or "").strip().replace("\\", "/")
    if not rel or ".." in Path(rel).parts or rel.startswith("/"):
        return None
    root = INSTANCE_DIR.resolve()
    path = (INSTANCE_DIR / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    if not path.is_file():
        return None
    if path.suffix.lower().lstrip(".") not in _MIME:
        return None
    return path


def mime_documento(path: Path) -> str:
    return _MIME.get(path.suffix.lower().lstrip("."), "application/octet-stream")


def salva_documento_economo(file: FileStorage, chiave: str) -> str | None:
    """Salva file e ritorna path relativo a INSTANCE_DIR, o None se non valido."""
    if not file or not file.filename:
        return None
    ext = estensione_consentita(file.filename)
    if not ext:
        return None
    fname = secure_filename(f"{chiave}.{ext}")
    path, _ = salva_upload(file, _dir_documenti(), fname)
    return str(path.relative_to(INSTANCE_DIR).as_posix())
