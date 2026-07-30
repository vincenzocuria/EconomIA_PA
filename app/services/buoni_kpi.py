"""Indicatori aggregati per elenco buoni (anno)."""

from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models.buono import BuonoEconomale, StatoBuono
from app.services.buoni_filtri import STATI_APERTI, STATI_DA_CHIUDERE


def kpi_buoni_anno(anno: int) -> dict:
    base = BuonoEconomale.query.filter_by(anno=anno)
    n_tot = base.count()
    n_aperti = base.filter(BuonoEconomale.stato.in_(STATI_APERTI)).count()
    n_da_chiudere = base.filter(BuonoEconomale.stato.in_(STATI_DA_CHIUDERE)).count()
    n_chiusi = base.filter_by(stato=StatoBuono.chiuso).count()

    sum_auth, sum_speso = (
        db.session.query(
            func.coalesce(func.sum(BuonoEconomale.importo_autorizzato), 0),
            func.coalesce(func.sum(BuonoEconomale.importo_speso), 0),
        )
        .filter(
            BuonoEconomale.anno == anno,
            BuonoEconomale.stato != StatoBuono.annullato,
        )
        .one()
    )
    tot_auth = Decimal(str(sum_auth))
    tot_speso = Decimal(str(sum_speso))
    return {
        "n_tot": n_tot,
        "n_aperti": n_aperti,
        "n_da_chiudere": n_da_chiudere,
        "n_chiusi": n_chiusi,
        "tot_autorizzato": tot_auth,
        "tot_speso": tot_speso,
        "residuo": tot_auth - tot_speso,
    }
