"""Formattazione data/ora movimento per viste."""

from app.models.movimento import Movimento


def testo_filiale_per_movimento(m: Movimento) -> str:
    if getattr(m, "filiale", None) is not None:
        return (m.filiale.denominazione or "").strip()
    return (getattr(m, "filiale_banca", None) or "").strip()


def formato_data_ora(m: Movimento) -> str:
    base = m.data_movimento.strftime("%d/%m/%Y")
    if getattr(m, "ora_movimento", None):
        return f"{base} {m.ora_movimento.strftime('%H:%M')}"
    return base


def dettaglio_banca_breve(m: Movimento) -> str:
    parts: list[str] = []
    if getattr(m, "ora_movimento", None):
        parts.append(m.ora_movimento.strftime("%H:%M"))
    fb = testo_filiale_per_movimento(m)
    if fb:
        parts.append(fb[:50])
    rr = (getattr(m, "rif_ricevuta", None) or "").strip()
    if rr:
        parts.append(f"Ricev. {rr[:40]}")
    return " — ".join(parts) if parts else ""
