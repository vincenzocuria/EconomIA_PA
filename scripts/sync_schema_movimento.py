"""Aggiorna lo schema SQLite per campi movimento banca (eseguibile anche senza avvio web)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.services.schema_filiale import applica_schema_filiale_banca
from app.services.schema_movimento import applica_patch_movimento


def main() -> None:
    app = create_app()
    with app.app_context():
        applica_patch_movimento()
        applica_schema_filiale_banca()
        print("Schema movimento + filiali banca aggiornato.")


if __name__ == "__main__":
    main()
