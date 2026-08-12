"""Buoni aperti senza modulo firmato ricaricato."""

from sqlalchemy import exists

from app.models.allegato import Allegato, TipoAllegato
from app.models.buono import BuonoEconomale, StatoBuono
from app.services.buoni_filtri import STATI_APERTI


def query_senza_firma(anno: int):
    """Buoni non chiusi/annullati senza allegato di tipo autorizzazione (modulo firmato)."""
    ha_firmato = exists().where(
        Allegato.buono_id == BuonoEconomale.id,
        Allegato.tipo_documento == TipoAllegato.autorizzazione,
    )
    return (
        BuonoEconomale.query.filter(
            BuonoEconomale.anno == anno,
            BuonoEconomale.stato.in_(STATI_APERTI),
            ~ha_firmato,
        ).order_by(BuonoEconomale.numero_progressivo.desc())
    )


def conta_senza_firma(anno: int) -> int:
    return query_senza_firma(anno).count()


def ids_senza_firma(anno: int) -> set[int]:
    rows = query_senza_firma(anno).with_entities(BuonoEconomale.id).all()
    return {r[0] for r in rows}
