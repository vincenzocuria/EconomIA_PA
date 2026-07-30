"""Normalizzazione testo per anagrafiche."""


def pulisci_testo(valore: str | None, max_len: int = 300) -> str:
    testo = " ".join((valore or "").strip().split())
    return testo[:max_len] if testo else ""


def normalizza_chiave(valore: str | None) -> str:
    return pulisci_testo(valore).casefold()
