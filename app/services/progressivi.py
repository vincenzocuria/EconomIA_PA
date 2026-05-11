from sqlalchemy import func, select

from app.extensions import db
from app.models.buono import BuonoEconomale
from app.models.movimento import Movimento


def prossimo_numero_movimento(anno: int) -> int:
    stmt = select(func.coalesce(func.max(Movimento.numero_progressivo), 0)).where(Movimento.anno == anno)
    n = db.session.scalar(stmt)
    return int(n or 0) + 1


def prossimo_numero_buono(anno: int) -> int:
    stmt = select(func.coalesce(func.max(BuonoEconomale.numero_progressivo), 0)).where(BuonoEconomale.anno == anno)
    n = db.session.scalar(stmt)
    return int(n or 0) + 1
