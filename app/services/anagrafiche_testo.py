"""Normalizzazione testo per anagrafiche."""

import re

_APOSTROFI = str.maketrans({
    "\u2019": "'",  # ’
    "\u2018": "'",  # ‘
    "\u02BC": "'",  # ʼ
    "`": "'",
    "´": "'",
})


def unifica_apostrofi(valore: str) -> str:
    return (valore or "").translate(_APOSTROFI)


def pulisci_testo(valore: str | None, max_len: int = 300) -> str:
    testo = unifica_apostrofi(valore or "")
    testo = " ".join(testo.strip().split())
    return testo[:max_len] if testo else ""


def _title_pezzo(pezzo: str) -> str:
    if not pezzo:
        return pezzo
    return pezzo[:1].upper() + pezzo[1:].lower()


def _title_parola(parola: str) -> str:
    """Title-case con apostrofo (D'Amico) e trattino (Maria-Luisa)."""
    parti = re.split(r"(['\-])", parola)
    out: list[str] = []
    for p in parti:
        if p in ("'", "-"):
            out.append(p)
        else:
            out.append(_title_pezzo(p))
    return "".join(out)


def normalizza_nome_persona(valore: str | None, max_len: int = 300) -> str:
    """Formato anagrafico persona: Zagarese Patrizia, D'Amico Salvatore."""
    testo = pulisci_testo(valore, max_len=max_len)
    if not testo:
        return ""
    return " ".join(_title_parola(p) for p in testo.split(" "))


def normalizza_denominazione(valore: str | None, max_len: int = 300) -> str:
    """Formato etichetta ufficio/ente: Ufficio Tecnico."""
    return normalizza_nome_persona(valore, max_len=max_len)


def normalizza_chiave(valore: str | None) -> str:
    """Chiave confronto: minuscolo, apostrofi unificati, spazi collassati."""
    return pulisci_testo(valore).casefold()
