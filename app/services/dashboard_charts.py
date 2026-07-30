"""Dati aggregati per i grafici della dashboard."""

from decimal import Decimal

from app.models.buono import BuonoEconomale, StatoBuono
from app.models.movimento import TipoMovimento
from app.services.cassa import effetto_su_cassa, movimenti_contabili

TIPI_ENTRATA = (
    TipoMovimento.entrata,
    TipoMovimento.reintegro,
    TipoMovimento.prelievo_banca,
)
TIPI_USCITA = (TipoMovimento.uscita, TipoMovimento.versamento_banca)


def _f(v: Decimal) -> float:
    return float(v)


def dati_grafici_dashboard(anno: int, saldo_iniziale_cassa: Decimal) -> dict:
    entrate = [0.0, 0.0, 0.0, 0.0]
    uscite = [0.0, 0.0, 0.0, 0.0]
    saldo_fine = [0.0, 0.0, 0.0, 0.0]
    cursore = Decimal(str(saldo_iniziale_cassa or 0))

    movs = sorted(
        movimenti_contabili(anno),
        key=lambda m: (m.trimestre or 1, m.data_movimento, m.numero_progressivo),
    )
    by_trim: dict[int, list] = {1: [], 2: [], 3: [], 4: []}
    for m in movs:
        t = m.trimestre if m.trimestre in (1, 2, 3, 4) else 1
        by_trim[t].append(m)

    for t in (1, 2, 3, 4):
        e = Decimal("0")
        u = Decimal("0")
        for m in by_trim[t]:
            if m.tipo in TIPI_ENTRATA:
                e += Decimal(str(m.importo or 0))
            elif m.tipo in TIPI_USCITA:
                u += Decimal(str(m.importo or 0))
            cursore += effetto_su_cassa(m)
        entrate[t - 1] = _f(e)
        uscite[t - 1] = _f(u)
        saldo_fine[t - 1] = _f(cursore)

    stati = [e.value for e in StatoBuono]
    counts = []
    for s in StatoBuono:
        counts.append(BuonoEconomale.query.filter_by(anno=anno, stato=s).count())

    return {
        "trimestri": {
            "labels": ["T1", "T2", "T3", "T4"],
            "entrate": entrate,
            "uscite": uscite,
            "saldo_cassa": saldo_fine,
        },
        "buoni_stato": {
            "labels": stati,
            "values": counts,
        },
    }
