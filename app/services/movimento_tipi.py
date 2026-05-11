"""Etichette UI per i tipi movimento (evita duplicati tra form e template)."""

from app.models.movimento import TipoMovimento

TIPO_MOVIMENTO_LABELS: dict[TipoMovimento, str] = {
    TipoMovimento.entrata: "Entrata",
    TipoMovimento.uscita: "Uscita",
    TipoMovimento.reintegro: "Reintegro cassa",
    TipoMovimento.rettifica: "Rettifica",
    TipoMovimento.storno: "Storno (uso tecnico)",
    TipoMovimento.prelievo_banca: "Prelievo contanti (banca → cassa)",
    TipoMovimento.versamento_banca: "Versamento contanti (cassa → banca)",
}


def scelte_tipo_movimento() -> list[tuple[str, str]]:
    return [(e.value, TIPO_MOVIMENTO_LABELS.get(e, e.value)) for e in TipoMovimento]
