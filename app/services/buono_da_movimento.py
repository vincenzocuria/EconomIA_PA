"""Precompilazione buono a partire da un movimento di uscita."""

from app.models.buono import BuonoEconomale, StatoBuono
from app.models.movimento import Movimento
from app.services.progressivi import prossimo_numero_buono
from app.services.sezionali_scelte import sezionale_default_buono


def valori_precompilati_da_movimento(m: Movimento) -> dict:
    sez = sezionale_default_buono()
    sez_id = sez.id if sez else m.sezionale_id
    num = prossimo_numero_buono(m.anno, sez_id) if sez_id else 1
    return {
        "anno": m.anno,
        "sezionale_id": sez_id or 0,
        "numero_progressivo": num,
        "data_buono": m.data_movimento,
        "causale": m.causale or "",
        "importo_autorizzato": m.importo,
        "importo_speso": m.importo,
        "beneficiario": m.beneficiario_fornitore or "",
        "stato": StatoBuono.bozza.value,
        "richiedente": "",
        "ufficio_richiedente": "",
        "note": "",
        "movimento_id": m.id,
    }


def collega_movimento_a_buono(m: Movimento, b: BuonoEconomale) -> None:
    m.buono_id = b.id
