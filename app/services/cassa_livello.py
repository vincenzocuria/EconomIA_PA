"""Classificazione visuale del saldo cassa (soglie fisse in euro)."""
from decimal import Decimal


def _dec(v) -> Decimal:
    return Decimal(str(v or 0))


def livello_cassa(importo) -> str:
    """Ritorna: ok | attenzione | basso | critico."""
    v = _dec(importo)
    if v > 100:
        return "ok"
    if v >= 50:
        return "attenzione"
    if v > 0:
        return "basso"
    return "critico"


def badge_cassa(importo) -> dict:
    """Metadati UI per badge Bootstrap sulla cassa attuale."""
    livello = livello_cassa(importo)
    mappa = {
        "ok": {"label": "ok", "classe": "text-bg-success"},
        "attenzione": {"label": "attenzione", "classe": "text-bg-warning"},
        "basso": {"label": "basso", "classe": "text-bg-cassa-basso"},
        "critico": {"label": "critico", "classe": "text-bg-danger"},
    }
    return {"livello": livello, **mappa[livello]}
