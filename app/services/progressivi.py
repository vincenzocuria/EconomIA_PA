from sqlalchemy import func, select

from app.extensions import db
from app.models.buono import BuonoEconomale
from app.models.movimento import Movimento


def prossimo_numero_movimento(anno: int, sezionale_id: int | None) -> int:
    stmt = select(func.coalesce(func.max(Movimento.numero_progressivo), 0)).where(
        Movimento.anno == anno,
        Movimento.sezionale_id == sezionale_id,
    )
    n = db.session.scalar(stmt)
    return int(n or 0) + 1


def prossimo_numero_buono(anno: int, sezionale_id: int | None) -> int:
    stmt = select(func.coalesce(func.max(BuonoEconomale.numero_progressivo), 0)).where(
        BuonoEconomale.anno == anno,
        BuonoEconomale.sezionale_id == sezionale_id,
    )
    n = db.session.scalar(stmt)
    return int(n or 0) + 1


def numero_movimento_libero(
    anno: int,
    sezionale_id: int | None,
    numero: int,
    escludi_id: int | None = None,
) -> bool:
    q = Movimento.query.filter_by(
        anno=anno,
        sezionale_id=sezionale_id,
        numero_progressivo=numero,
    )
    if escludi_id:
        q = q.filter(Movimento.id != escludi_id)
    return q.first() is None


def numero_buono_libero(
    anno: int,
    sezionale_id: int | None,
    numero: int,
    escludi_id: int | None = None,
) -> bool:
    q = BuonoEconomale.query.filter_by(
        anno=anno,
        sezionale_id=sezionale_id,
        numero_progressivo=numero,
    )
    if escludi_id:
        q = q.filter(BuonoEconomale.id != escludi_id)
    return q.first() is None
