"""Formato visualizzazione progressivi con sezionale (es. GEN-0003/2026)."""


def formato_numero_sezionale(obj) -> str:
    """obj: Movimento o BuonoEconomale con anno, numero_progressivo, sezionale opzionale."""
    codice = ""
    sez = getattr(obj, "sezionale", None)
    if sez is not None and getattr(sez, "codice", None):
        codice = sez.codice
    elif getattr(obj, "sezionale_id", None):
        codice = "?"
    num = int(getattr(obj, "numero_progressivo", 0) or 0)
    anno = getattr(obj, "anno", "")
    if codice:
        return f"{codice}-{num:04d}/{anno}"
    return f"{num:04d}/{anno}"
