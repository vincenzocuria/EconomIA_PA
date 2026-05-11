"""Salvataggio sicuro allegati con nome strutturato e validazione MIME/estensione."""
import re
from datetime import date
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.models.allegato import TipoAllegato
from app.services.file_hash import sha256_file


def estensione_consentita(name: str) -> str | None:
    if not name or "." not in name:
        return None
    ext = name.rsplit(".", 1)[-1].lower()
    allowed = current_app.config.get("UPLOAD_ALLOWED_EXT", frozenset())
    return ext if ext in allowed else None


def mime_consentito_per_estensione(mime: str, ext: str) -> bool:
    m = (mime or "").lower()
    ok = {
        "pdf": ("application/pdf",),
        "jpg": ("image/jpeg",),
        "jpeg": ("image/jpeg",),
        "png": ("image/png",),
        "webp": ("image/webp",),
    }
    return m in ok.get(ext, ())


def slug_sicuro(s: str, max_len: int = 40) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9._-]", "", s, flags=re.I)
    return (s[:max_len] or "doc").rstrip(".")


def nome_file_allegato(
    data_doc: date,
    prefisso: str,
    num_prog: int,
    tipo: TipoAllegato,
    beneficiario: str,
    importo: str,
    ext: str,
) -> str:
    d = data_doc.isoformat()
    ben = slug_sicuro(beneficiario or "sconosciuto", 30)
    imp = slug_sicuro(str(importo).replace(",", "."), 12)
    tipo_s = tipo.value if hasattr(tipo, "value") else str(tipo)
    return f"{d}_{prefisso}-{num_prog:04d}_{tipo_s}_{ben}-{imp}.{ext}"


def salva_upload(
    file: FileStorage,
    dest_dir: Path,
    nome_finale: str,
) -> tuple[Path, str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe = secure_filename(nome_finale)
    path = dest_dir / safe
    file.save(str(path))
    digest = sha256_file(path)
    return path, digest
