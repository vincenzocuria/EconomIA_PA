"""Movimenti uscita/banca senza allegato collegato."""

from sqlalchemy import exists

from app.models.allegato import Allegato
from app.models.movimento import Movimento, StatoMovimento, TipoMovimento

TIPI_SENZA_ALLEGATO = (
    TipoMovimento.uscita,
    TipoMovimento.versamento_banca,
    TipoMovimento.prelievo_banca,
)


def query_senza_allegato(anno: int):
    ha_allegato = exists().where(Allegato.movimento_id == Movimento.id)
    return (
        Movimento.query.filter(
            Movimento.anno == anno,
            Movimento.stato != StatoMovimento.stornato,
            Movimento.tipo.in_(TIPI_SENZA_ALLEGATO),
            ~ha_allegato,
        ).order_by(Movimento.numero_progressivo.desc())
    )


def conta_senza_allegato(anno: int) -> int:
    return query_senza_allegato(anno).count()
