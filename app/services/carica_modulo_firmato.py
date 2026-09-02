"""Carica il modulo rimborso firmato su un buono."""
from werkzeug.datastructures import FileStorage

from app.models.allegato import TipoAllegato
from app.models.buono import BuonoEconomale
from app.services.allega_a_buono import allega_file_a_buono


def carica_modulo_firmato(
    b: BuonoEconomale,
    file: FileStorage | None,
) -> tuple[bool, str | None]:
    """(caricato, errore). caricato=False e errore=None se manca il file."""
    if not file or not getattr(file, "filename", None):
        return False, None
    _, err = allega_file_a_buono(b, file, TipoAllegato.autorizzazione)
    return err is None, err
