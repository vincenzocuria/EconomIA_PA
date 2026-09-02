"""Testo anagrafico dell'economo (intestazioni e moduli)."""

from app.models.economo import EconomoSettings


def nome_da_economo(eco: EconomoSettings | None) -> str:
    if not eco:
        return ""
    return " ".join(x.strip() for x in (eco.nome, eco.cognome) if (x or "").strip())
