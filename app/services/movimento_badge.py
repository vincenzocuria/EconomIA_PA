"""Badge sintetici per tipo e stato movimento."""

from app.models.movimento import StatoMovimento, TipoMovimento
from app.services.movimento_tipi import TIPO_MOVIMENTO_LABELS

_TIPO = {
    TipoMovimento.entrata: ("Entrata", "text-bg-success"),
    TipoMovimento.uscita: ("Uscita", "text-bg-danger"),
    TipoMovimento.reintegro: ("Reintegro", "text-bg-success"),
    TipoMovimento.prelievo_banca: ("Prelievo", "text-bg-primary"),
    TipoMovimento.versamento_banca: ("Versamento", "text-bg-info"),
    TipoMovimento.rettifica: ("Rettifica", "text-bg-warning"),
    TipoMovimento.storno: ("Storno", "text-bg-dark"),
}

_STATO = {
    StatoMovimento.registrato: ("Registrato", "text-bg-secondary"),
    StatoMovimento.rendicontato: ("Rendicontato", "text-bg-success"),
    StatoMovimento.stornato: ("Stornato", "text-bg-dark"),
    StatoMovimento.rettificato: ("Rettificato", "text-bg-warning"),
}


def badge_tipo(tipo: TipoMovimento) -> tuple[str, str, str]:
    breve, classe = _TIPO.get(tipo, (getattr(tipo, "value", str(tipo)), "text-bg-secondary"))
    titolo = TIPO_MOVIMENTO_LABELS.get(tipo, breve)
    return breve, classe, titolo


def badge_stato(stato: StatoMovimento) -> tuple[str, str]:
    return _STATO.get(stato, (getattr(stato, "value", str(stato)), "text-bg-secondary"))


def scelte_stato_movimento() -> list[tuple[str, str]]:
    return [(stato.value, etichetta) for stato, (etichetta, _classe) in _STATO.items()]
