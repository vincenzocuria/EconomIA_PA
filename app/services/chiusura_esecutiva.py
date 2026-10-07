"""Chiusura e riapertura del trimestre, con archivio delle stampe e mail."""

from datetime import datetime, timezone

from flask_login import current_user

from app.config import INSTANCE_DIR
from app.extensions import db
from app.services.audit_log import scrivi_audit
from app.services.chiusura_checklist import controlla_chiusura
from app.services.chiusura_documenti import dir_chiusura
from app.services.chiusura_mail import invia_notifica_chiusura, invia_notifica_riapertura
from app.services.chiusura_record import ottieni_chiusura
from app.services.incarico_periodo import trimestre_dovuto
from app.services.pdf_giornale_cassa import genera_giornale_cassa
from app.services.pdf_prospetto_pagamenti import genera_prospetto_pagamenti


def _rel(path) -> str:
    return path.relative_to(INSTANCE_DIR).as_posix()


def _utente_id() -> int | None:
    if current_user.is_authenticated:
        return current_user.id
    return None


def chiudi_trimestre(anno: int, trimestre: int) -> tuple[bool, str]:
    if not trimestre_dovuto(anno, trimestre):
        return False, "Il trimestre non è ancora terminato: la chiusura si fa a periodo concluso."
    esito = controlla_chiusura(anno, trimestre)
    if esito["chiusa"]:
        return False, "Questo trimestre è già chiuso."
    if not esito["pronto"]:
        return False, f"Chiusura bloccata: mancano ancora {esito['n_mancanti']} controlli."

    row = ottieni_chiusura(anno, trimestre, crea=True)
    cartella = dir_chiusura(anno, trimestre)
    prospetto = genera_prospetto_pagamenti(anno, trimestre, cartella / f"prospetto_pagamenti_{anno}_T{trimestre}.pdf")
    giornale = genera_giornale_cassa(anno, trimestre, cartella / f"giornale_cassa_{anno}_T{trimestre}.pdf")
    row.prospetto_path = _rel(prospetto)
    row.giornale_path = _rel(giornale)
    row.stato = "chiusa"
    row.chiusa_il = datetime.now(timezone.utc).replace(tzinfo=None)
    row.chiusa_da_id = _utente_id()
    db.session.commit()
    scrivi_audit(
        "chiusura_trimestre",
        row.id,
        "chiusura",
        {"anno": anno, "trimestre": trimestre, "mancanti": 0},
    )
    ok, msg = invia_notifica_chiusura(anno, trimestre, chiusa=True)
    if ok:
        return True, "Trimestre chiuso. Notifica inviata."
    return True, f"Trimestre chiuso. Notifica non inviata: {msg}"


def riapri_trimestre(anno: int, trimestre: int) -> tuple[bool, str]:
    row = ottieni_chiusura(anno, trimestre, crea=False)
    if row is None or row.stato != "chiusa":
        return False, "Il trimestre non risulta chiuso."
    row.stato = "aperta"
    row.riaperta_il = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()
    scrivi_audit("chiusura_trimestre", row.id, "riapertura", {"anno": anno, "trimestre": trimestre})
    ok, msg = invia_notifica_riapertura(anno, trimestre)
    if ok:
        return True, "Trimestre riaperto. Notifica inviata."
    return True, f"Trimestre riaperto. Notifica non inviata: {msg}"
