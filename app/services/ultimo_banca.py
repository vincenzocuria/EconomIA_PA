"""Ultimo movimento per tipo (esclusi stornati)."""
from app.models.movimento import Movimento, StatoMovimento, TipoMovimento


def ultimo_movimento_tipo(anno: int, tipo: TipoMovimento) -> Movimento | None:
    return (
        Movimento.query.filter(
            Movimento.anno == anno,
            Movimento.tipo == tipo,
            Movimento.stato != StatoMovimento.stornato,
        )
        .order_by(Movimento.data_movimento.desc(), Movimento.numero_progressivo.desc())
        .first()
    )


def ultimo_prelievo(anno: int) -> Movimento | None:
    return ultimo_movimento_tipo(anno, TipoMovimento.prelievo_banca)


def ultimo_versamento(anno: int) -> Movimento | None:
    return ultimo_movimento_tipo(anno, TipoMovimento.versamento_banca)
