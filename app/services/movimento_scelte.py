"""Etichette per select che collegano un movimento (allegati, ecc.)."""

from app.models.movimento import Movimento
from app.services.movimento_tipi import TIPO_MOVIMENTO_LABELS
from app.services.numero_display import formato_numero_sezionale


def etichetta_movimento_scelta(m: Movimento) -> str:
    """Es. GEN-0003/2026 — Prelievo contanti (banca → cassa) — € 250,00 — causale…"""
    tipo = TIPO_MOVIMENTO_LABELS.get(m.tipo, m.tipo.value if hasattr(m.tipo, "value") else str(m.tipo))
    try:
        imp = f"€ {float(m.importo):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        imp = str(m.importo)
    data = m.data_movimento.strftime("%d/%m/%Y") if m.data_movimento else ""
    parti = [formato_numero_sezionale(m), data, tipo, imp]
    causale = (m.causale or "").strip()
    if causale:
        parti.append(causale[:28])
    return " — ".join(p for p in parti if p)


def scelte_movimento(anno: int) -> list[tuple[int, str]]:
    opts = [(0, "— Nessun movimento —")]
    rows = (
        Movimento.query.filter_by(anno=anno)
        .order_by(Movimento.numero_progressivo.desc())
        .all()
    )
    for m in rows:
        opts.append((m.id, etichetta_movimento_scelta(m)))
    return opts
