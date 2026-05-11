"""Calcolo saldi e totali da movimenti (esclusi quelli con stato stornato)."""
from decimal import Decimal

from app.models.movimento import Movimento, StatoMovimento, TipoMovimento


def _dec(v) -> Decimal:
    return Decimal(str(v or 0))


def effetto_su_saldo(m: Movimento) -> Decimal:
    v = _dec(m.importo)
    t = m.tipo
    if t in (TipoMovimento.entrata, TipoMovimento.reintegro, TipoMovimento.prelievo_banca):
        return v
    if t in (TipoMovimento.uscita, TipoMovimento.versamento_banca):
        return -v
    return v


def movimenti_contabili(anno: int):
    return (
        Movimento.query.filter(
            Movimento.anno == anno,
            Movimento.stato != StatoMovimento.stornato,
        )
        .order_by(Movimento.numero_progressivo)
        .all()
    )


def totale_entrate(anno: int) -> Decimal:
    return sum(
        (
            _dec(m.importo)
            for m in movimenti_contabili(anno)
            if m.tipo in (TipoMovimento.entrata, TipoMovimento.reintegro, TipoMovimento.prelievo_banca)
        ),
        start=Decimal("0"),
    )


def totale_uscite(anno: int) -> Decimal:
    return sum(
        (
            _dec(m.importo)
            for m in movimenti_contabili(anno)
            if m.tipo in (TipoMovimento.uscita, TipoMovimento.versamento_banca)
        ),
        start=Decimal("0"),
    )


def saldo_calcolato(anno: int, saldo_iniziale: Decimal) -> Decimal:
    delta = sum((effetto_su_saldo(m) for m in movimenti_contabili(anno)), start=Decimal("0"))
    return saldo_iniziale + delta
