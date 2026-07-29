"""Helper per il flag da_giustificare sui movimenti."""

from app.models.movimento import Movimento


def segna_giustificato(m: Movimento | None) -> bool:
    """Azzera da_giustificare se attivo. Ritorna True se ha modificato."""
    if m is None or not m.da_giustificare:
        return False
    m.da_giustificare = False
    return True
