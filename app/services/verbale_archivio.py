"""Salvataggio PDF verbali ufficiali di verifica cassa."""
from datetime import date
from pathlib import Path

from werkzeug.datastructures import FileStorage

from app.config import INSTANCE_DIR
from app.services.upload_allegato import salva_upload


def dir_verbali_ufficiali() -> Path:
    return INSTANCE_DIR / "verbali" / "ufficiali"


def nome_file_verbale_verifica(
    data_verbale: date,
    anno: int,
    trimestre: int,
    numero: int,
    ext: str = "pdf",
) -> str:
    return (
        f"{data_verbale.isoformat()}_verbale-verifica_"
        f"{anno}_T{trimestre}_n{numero}.{ext}"
    )


def salva_pdf_verbale(
    file: FileStorage,
    data_verbale: date,
    anno: int,
    trimestre: int,
    numero: int,
    ext: str = "pdf",
) -> tuple[Path, str, str]:
    """Salva PDF; restituisce path assoluto, path relativo a INSTANCE_DIR, sha256."""
    nome = nome_file_verbale_verifica(data_verbale, anno, trimestre, numero, ext)
    dest = dir_verbali_ufficiali()
    path, digest = salva_upload(file, dest, nome)
    rel = str(path.relative_to(INSTANCE_DIR)).replace("\\", "/")
    return path, rel, digest
