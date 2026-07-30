"""Risoluzione path assoluto del logo ente (impostazioni)."""
from pathlib import Path

from app.config import INSTANCE_DIR
from app.extensions import db
from app.models.ente import EnteSettings

_ESTENSIONI_OK = frozenset({"png", "jpg", "jpeg", "webp", "gif", "bmp"})


def logo_ente_path() -> Path | None:
    row = db.session.get(EnteSettings, 1)
    if not row or not (row.logo_path or "").strip():
        return None
    rel = row.logo_path.strip().replace("\\", "/")
    if ".." in Path(rel).parts or rel.startswith("/"):
        return None
    root = INSTANCE_DIR.resolve()
    path = (INSTANCE_DIR / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    if not path.is_file():
        return None
    ext = path.suffix.lower().lstrip(".")
    if ext not in _ESTENSIONI_OK:
        return None
    return path
