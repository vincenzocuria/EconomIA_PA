"""Formato importi in euro per le viste."""


def formato_euro(v, con_segno: bool = False) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "€ —"
    corpo = f"{abs(n):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if n < 0:
        return f"€ -{corpo}"
    if con_segno and n > 0:
        return f"€ +{corpo}"
    return f"€ {corpo}"
