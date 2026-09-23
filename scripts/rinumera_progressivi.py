"""Ricompatta una volta i progressivi per sezionale e rinomina gli allegati."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.models.buono import BuonoEconomale
from app.models.movimento import Movimento
from app.services.numero_display import formato_numero_sezionale
from app.services.rinumera_progressivi import rinumera_progressivi


def main() -> None:
    app = create_app()
    with app.app_context():
        log = rinumera_progressivi()
        for riga in log:
            print(riga)
        print("--- buoni ---")
        for b in BuonoEconomale.query.order_by(
            BuonoEconomale.sezionale_id, BuonoEconomale.numero_progressivo
        ):
            print(formato_numero_sezionale(b), b.data_buono, b.richiedente)
        print("--- movimenti ---")
        for m in Movimento.query.order_by(
            Movimento.sezionale_id, Movimento.numero_progressivo
        ):
            print(formato_numero_sezionale(m), m.data_movimento, m.tipo)
        if not log:
            print("Nessun file rinominato.")


if __name__ == "__main__":
    main()
