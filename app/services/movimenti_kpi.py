"""Indicatori aggregati per il registro movimenti (anno)."""

from decimal import Decimal

from app.models.cassetto import SaldoAnnuale
from app.models.movimento import Movimento, StatoMovimento, TipoMovimento
from app.services.cassa import (
    saldo_cassa_calcolato,
    saldo_conto_calcolato,
    totale_entrate,
    totale_uscite,
)
from app.services.cassa_livello import badge_cassa
from app.services.movimenti_senza_allegato import conta_senza_allegato


def _saldi_iniziali(anno: int) -> tuple[Decimal, Decimal]:
    row = SaldoAnnuale.query.get(anno)
    if row is None:
        return Decimal("0"), Decimal("0")
    cassa = Decimal(str(row.saldo_iniziale or 0))
    conto = Decimal(str(getattr(row, "saldo_conto_iniziale", 0) or 0))
    return cassa, conto


def kpi_movimenti_anno(anno: int) -> dict:
    base = Movimento.query.filter_by(anno=anno)
    ini_cassa, ini_conto = _saldi_iniziali(anno)
    saldo_cassa = saldo_cassa_calcolato(anno, ini_cassa)
    n_giust = (
        base.filter_by(da_giustificare=True)
        .filter(Movimento.stato != StatoMovimento.stornato)
        .count()
    )
    return {
        "n_tot": base.count(),
        "n_uscite": base.filter_by(tipo=TipoMovimento.uscita).count(),
        "n_prelievi": base.filter_by(tipo=TipoMovimento.prelievo_banca).count(),
        "n_versamenti": base.filter_by(tipo=TipoMovimento.versamento_banca).count(),
        "n_da_giustificare": n_giust,
        "n_senza_allegato": conta_senza_allegato(anno),
        "saldo_cassa": saldo_cassa,
        "saldo_conto": saldo_conto_calcolato(anno, ini_conto),
        "badge_cassa": badge_cassa(saldo_cassa),
        "tot_entrate": totale_entrate(anno),
        "tot_uscite": totale_uscite(anno),
    }
