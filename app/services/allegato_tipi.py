"""Etichette UI per i tipi allegato."""

from app.models.allegato import TipoAllegato

TIPO_ALLEGATO_LABELS: dict[TipoAllegato, str] = {
    TipoAllegato.scontrino: "Scontrino",
    TipoAllegato.fattura: "Fattura",
    TipoAllegato.ricevuta: "Ricevuta",
    TipoAllegato.richiesta_ufficio: "Richiesta ufficio",
    TipoAllegato.autorizzazione: "Autorizzazione",
    TipoAllegato.determina: "Determina",
    TipoAllegato.verbale: "Verbale",
    TipoAllegato.estratto_conto: "Estratto conto",
    TipoAllegato.altro: "Altro",
}


def scelte_tipo_allegato() -> list[tuple[str, str]]:
    return [(e.value, TIPO_ALLEGATO_LABELS.get(e, e.value)) for e in TipoAllegato]
