"""Formato visualizzazione progressivi con sezionale (es. GEN-0003/2026)."""


def codice_sezionale(obj) -> str:
    """Codice sezionale, '?' se l'id c'è ma la relazione no, stringa vuota se assente."""
    sez = getattr(obj, "sezionale", None)
    if sez is not None and getattr(sez, "codice", None):
        return str(sez.codice)
    if getattr(obj, "sezionale_id", None):
        return "?"
    return ""


def formato_numero_sezionale(obj) -> str:
    """obj: Movimento o BuonoEconomale con anno, numero_progressivo, sezionale opzionale."""
    codice = codice_sezionale(obj)
    num = int(getattr(obj, "numero_progressivo", 0) or 0)
    anno = getattr(obj, "anno", "")
    if codice:
        return f"{codice}-{num:04d}/{anno}"
    return f"{num:04d}/{anno}"


def parte_file_progressivo(obj) -> str:
    """Parte nome file: RIM_0001, oppure 0001 se manca il sezionale."""
    num = int(getattr(obj, "numero_progressivo", 0) or 0)
    codice = codice_sezionale(obj)
    num_s = f"{num:04d}"
    if codice and codice != "?":
        return f"{codice}_{num_s}"
    return num_s
