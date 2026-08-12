"""Recupera il responsabile associato a un ufficio in anagrafica."""

from app.models.anagrafica_ufficio import AnagraficaUfficio
from app.services.anagrafiche_testo import normalizza_chiave, pulisci_testo


def responsabile_per_ufficio(denominazione: str | None) -> str:
    nome = pulisci_testo(denominazione)
    if not nome:
        return ""
    row = AnagraficaUfficio.query.filter_by(
        denominazione_norm=normalizza_chiave(nome)
    ).first()
    if row is None:
        return ""
    return pulisci_testo(row.responsabile)
