"""Saldi di cassa e conto limitati a un trimestre, e scostamento rispetto all'estratto."""

from datetime import date
from decimal import Decimal

from app.models.cassetto import SaldoAnnuale
from app.models.chiusura_trimestre import ChiusuraTrimestre
from app.models.movimento import Movimento, StatoMovimento, TipoMovimento
from app.services.alerts import fine_trimestre
from app.services.cassa import effetto_su_cassa, effetto_su_conto

CENT = Decimal("0.01")


def inizio_trimestre(anno: int, trimestre: int) -> date:
    mese = (trimestre - 1) * 3 + 1
    return date(anno, mese, 1)


def _centesimi(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(CENT)


def _saldi_anno(anno: int) -> tuple[Decimal, Decimal]:
    row = SaldoAnnuale.query.get(anno)
    cassa = _centesimi(row.saldo_iniziale) if row else Decimal("0.00")
    conto = _centesimi(getattr(row, "saldo_conto_iniziale", 0) if row else 0)
    return cassa, conto


def movimenti_attivi(anno: int) -> list[Movimento]:
    return (
        Movimento.query.filter(
            Movimento.anno == anno,
            Movimento.stato != StatoMovimento.stornato,
        )
        .order_by(Movimento.data_movimento, Movimento.numero_progressivo)
        .all()
    )


def quadratura_trimestre(
    anno: int,
    trimestre: int,
    chiusura: ChiusuraTrimestre | None,
    movimenti: list[Movimento] | None = None,
) -> dict:
    inizio = inizio_trimestre(anno, trimestre)
    fine = fine_trimestre(anno, trimestre)
    tutti = movimenti if movimenti is not None else movimenti_attivi(anno)
    ini_cassa, ini_conto = _saldi_anno(anno)

    cassa = ini_cassa
    conto = ini_conto
    giacenza_inizio = ini_cassa
    conto_inizio = ini_conto
    nel: list[Movimento] = []
    for m in tutti:
        if m.data_movimento < inizio:
            cassa += effetto_su_cassa(m)
            conto += effetto_su_conto(m)
            giacenza_inizio = cassa
            conto_inizio = conto
            continue
        if m.data_movimento <= fine:
            nel.append(m)
            cassa += effetto_su_cassa(m)
            conto += effetto_su_conto(m)

    uscite = [m for m in nel if m.tipo == TipoMovimento.uscita]
    prelievi = [m for m in nel if m.tipo == TipoMovimento.prelievo_banca]
    versamenti = [m for m in nel if m.tipo == TipoMovimento.versamento_banca]
    entrate = [m for m in nel if m.tipo in (TipoMovimento.entrata, TipoMovimento.reintegro)]

    totale_uscite = sum((_centesimi(m.importo) for m in uscite), start=Decimal("0.00"))
    totale_prelievi = sum((_centesimi(m.importo) for m in prelievi), start=Decimal("0.00"))
    totale_versamenti = sum((_centesimi(m.importo) for m in versamenti), start=Decimal("0.00"))
    totale_entrate = sum((_centesimi(m.importo) for m in entrate), start=Decimal("0.00"))

    voci = list(chiusura.voci_conto) if chiusura is not None else []
    somma_voci = sum((_centesimi(v.importo) for v in voci), start=Decimal("0.00"))
    delta_conto = _centesimi(conto - conto_inizio)

    saldo_ini = chiusura.saldo_estratto_iniziale if chiusura is not None else None
    saldo_fin = chiusura.saldo_estratto_finale if chiusura is not None else None
    delta_estratto = None
    scostamento = None
    if saldo_ini is not None and saldo_fin is not None:
        delta_estratto = _centesimi(saldo_fin) - _centesimi(saldo_ini)
        scostamento = _centesimi(delta_estratto - delta_conto - somma_voci)

    return {
        "inizio": inizio,
        "fine": fine,
        "nel": nel,
        "uscite": uscite,
        "prelievi": prelievi,
        "versamenti": versamenti,
        "entrate": entrate,
        "totale_uscite": totale_uscite,
        "totale_prelievi": totale_prelievi,
        "totale_versamenti": totale_versamenti,
        "totale_entrate": totale_entrate,
        "giacenza_inizio": _centesimi(giacenza_inizio),
        "giacenza_fine": _centesimi(cassa),
        "conto_inizio": _centesimi(conto_inizio),
        "conto_fine": _centesimi(conto),
        "delta_conto": delta_conto,
        "voci": voci,
        "somma_voci": somma_voci,
        "delta_estratto": delta_estratto,
        "scostamento": scostamento,
        "saldi_estratto_inseriti": saldo_ini is not None and saldo_fin is not None,
    }
