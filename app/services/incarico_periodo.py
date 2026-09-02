"""Trimestri coperti dall'incarico dell'economo (incarico_dal)."""
from datetime import date

from app.models.economo import EconomoSettings
from app.models.movimento import trimestre_da_data


def data_incarico() -> date | None:
    row = EconomoSettings.query.get(1)
    return row.incarico_dal if row else None


def trimestri_in_incarico(anno: int, dal: date | None = None) -> list[int]:
    """T1–T4 dell'anno coperti dall'incarico. Senza data: tutto l'anno."""
    if dal is None:
        dal = data_incarico()
    if dal is None:
        return [1, 2, 3, 4]
    if anno < dal.year:
        return []
    if anno > dal.year:
        return [1, 2, 3, 4]
    inizio = trimestre_da_data(dal)
    return [t for t in (1, 2, 3, 4) if t >= inizio]


def trimestre_in_incarico(anno: int, trimestre: int, dal: date | None = None) -> bool:
    return trimestre in trimestri_in_incarico(anno, dal)


def trimestre_dovuto(anno: int, trimestre: int, oggi: date | None = None) -> bool:
    """True se il trimestre è in incarico e già chiuso."""
    from app.services.alerts import fine_trimestre

    oggi = oggi or date.today()
    if not trimestre_in_incarico(anno, trimestre):
        return False
    if oggi.year == anno and trimestre > trimestre_da_data(oggi):
        return False
    chiuso = anno < oggi.year or (anno == oggi.year and fine_trimestre(anno, trimestre) < oggi)
    return chiuso


def trimestre_default_form(anno: int, oggi: date | None = None) -> int | None:
    """Trimestre corrente, limitato al range dell'incarico."""
    oggi = oggi or date.today()
    disp = trimestri_in_incarico(anno)
    if not disp:
        return None
    if anno == oggi.year:
        corrente = trimestre_da_data(oggi)
    elif anno < oggi.year:
        corrente = 4
    else:
        corrente = 1
    if corrente in disp:
        return corrente
    if corrente < disp[0]:
        return disp[0]
    return disp[-1]


def scelte_trimestre(anno: int) -> list[tuple[int, str]]:
    return [(t, f"T{t}") for t in trimestri_in_incarico(anno)]
