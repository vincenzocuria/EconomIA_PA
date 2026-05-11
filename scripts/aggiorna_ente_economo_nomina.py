"""
Aggiorna ente_settings ed economo_settings (id=1) con i dati della nomina
delibera G.C. n. 22/2026 (Comune di San Lorenzo del Vallo — Ing. Vincenzo Curia).

Esegui dalla cartella del progetto:
  .venv\\Scripts\\python.exe scripts\\aggiorna_ente_economo_nomina.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app import create_app
from app.extensions import db
from app.models.economo import EconomoSettings
from app.models.ente import EnteSettings

# Fonte: PDF in LAVORAZIONE/ECONOMATO/Nomina (delibera, PEC, verbale consegna)
ENTE = {
    "denominazione": "Comune di San Lorenzo del Vallo",
    "codice_fiscale_ente": "01334140785",
    "codice_istat": "078122",
    "indirizzo": "Viale della Libertà 123",
    "cap": "87040",
    "comune": "San Lorenzo del Vallo",
    "provincia": "CS",
    "pec": "sanlorenzodelvallo@asmepec.it",
    "email": "",
    "telefono": "0981953103",
    "note_legali": (
        "Riferimenti nomina economo: D.G.C. n. 22 del 27/04/2026 (pubbl. Albo reg. 292, "
        "esecutiva 27/04/2026). Trasmissione Corte dei conti prot. GC-2026-00022 / "
        "prot. comunale 0003140 del 06/05/2026. Verbale consegna prot. 0003310 del 11/05/2026."
    ),
}

ECONOMO = {
    "cognome": "Curia",
    "nome": "Vincenzo",
    "codice_fiscale": "CRUVCN86B02D005U",
    "qualifica": "Economo comunale (Ing.) — C/1, profilo Istruttore informatico",
    "incarico_dal": date(2026, 4, 1),
    "delibera_nomina": (
        "D.G.C. n. 22 del 27/04/2026 — affidamento incarico economo comunale "
        "(trasmissione Corte dei conti GC-2026-00022, prot. 0003140 del 06/05/2026)"
    ),
    "telefono": "",
    "email": "",
    "note": (
        "Decorrenza incarico 1° aprile 2026 (cessazione precedente economo Ing. Luigi Garofalo). "
        "Sostituto in caso di assenza: Sig. Antonio Labanca (Polizia Municipale, C/1), "
        "come da stessa deliberazione."
    ),
}


def main() -> int:
    app = create_app()
    with app.app_context():
        ente = db.session.get(EnteSettings, 1)
        eco = db.session.get(EconomoSettings, 1)
        if not ente or not eco:
            print("ERRORE: mancano righe ente_settings/economo_settings id=1.", file=sys.stderr)
            return 1
        for k, v in ENTE.items():
            setattr(ente, k, v)
        for k, v in ECONOMO.items():
            setattr(eco, k, v)
        db.session.commit()
        print("Aggiornato ente_settings e economo_settings (id=1).")
        print("  Ente:", ente.denominazione, "| CF", ente.codice_fiscale_ente)
        print("  Economo:", eco.nome, eco.cognome, "| CF", eco.codice_fiscale)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
