"""Testo e invio della notifica di chiusura trimestre."""

import re
from datetime import datetime, timezone

from app.extensions import db
from app.models.economo import EconomoSettings
from app.models.ente import EnteSettings
from app.services.chiusura_checklist import controlla_chiusura
from app.services.chiusura_record import ottieni_chiusura
from app.services.euro import formato_euro
from app.services.mail_resend import invia_email


def destinatari_chiusura() -> list[str]:
    eco = EconomoSettings.query.get(1)
    ente = EnteSettings.query.get(1)
    blocchi = []
    if eco is not None:
        blocchi.append(eco.email or "")
        blocchi.append(getattr(eco, "email_chiusura", "") or "")
    if ente is not None:
        blocchi.append(ente.email or "")
        blocchi.append(ente.pec or "")
    visti: set[str] = set()
    out: list[str] = []
    for blocco in blocchi:
        for pezzo in re.split(r"[,;\n]+", blocco):
            email = pezzo.strip()
            if "@" not in email:
                continue
            chiave = email.lower()
            if chiave in visti:
                continue
            visti.add(chiave)
            out.append(email)
    return out


def _righe_stato(esito: dict) -> list[str]:
    righe = []
    for voce in esito["mancanti"]:
        righe.append(f"MANCA — {voce['titolo']}: {voce['dettaglio']}")
        for item in voce["mancanti"]:
            righe.append(f"    · {item['etichetta']}")
    for voce in esito["avvisi"]:
        righe.append(f"AVVISO — {voce['titolo']}: {voce['dettaglio']}")
    for voce in esito["presenti"]:
        righe.append(f"OK — {voce['titolo']}: {voce['dettaglio']}")
    return righe


def componi_notifica(anno: int, trimestre: int, esito: dict, *, chiusa: bool) -> tuple[str, str]:
    ente = EnteSettings.query.get(1)
    nome = ((ente.denominazione if ente else "") or "Ente").strip()
    q = esito["quadratura"]
    if chiusa:
        oggetto = f"{nome} — chiusura T{trimestre}/{anno} completata"
        testa = f"Il trimestre T{trimestre} {anno} della cassa economale è chiuso."
    elif esito["pronto"]:
        oggetto = f"{nome} — fascicolo T{trimestre}/{anno} pronto per la chiusura"
        testa = f"Il fascicolo T{trimestre} {anno} è completo: si può chiudere il trimestre."
    else:
        oggetto = f"{nome} — chiusura T{trimestre}/{anno}: mancano {esito['n_mancanti']} controlli"
        testa = (
            f"Chiusura T{trimestre} {anno} non eseguibile: "
            f"mancano {esito['n_mancanti']} controlli del fascicolo."
        )
    corpo = "\n".join(
        [
            testa,
            "",
            f"Giacenza di cassa a fine trimestre: {formato_euro(q['giacenza_fine'])}.",
            f"Pagamenti (buoni): {formato_euro(q['totale_uscite'])}.",
            f"Prelievi: {formato_euro(q['totale_prelievi'])}.",
            f"Variazione conto da registro: {formato_euro(q['delta_conto'])}.",
            "",
            "Stato del fascicolo",
            *(_righe_stato(esito) or ["Nessuna voce."]),
            "",
            "Messaggio generato da EconomIA_PA. Il registro locale non sostituisce il protocollo dell'ente.",
        ]
    )
    return oggetto, corpo


def _memorizza_esito(anno: int, trimestre: int, msg: str) -> None:
    row = ottieni_chiusura(anno, trimestre, crea=True)
    row.ultima_notifica_il = datetime.now(timezone.utc).replace(tzinfo=None)
    row.ultima_notifica_esito = msg[:500]
    db.session.commit()


def invia_notifica_chiusura(anno: int, trimestre: int, *, chiusa: bool) -> tuple[bool, str]:
    esito = controlla_chiusura(anno, trimestre)
    oggetto, corpo = componi_notifica(anno, trimestre, esito, chiusa=chiusa)
    ok, msg = invia_email(destinatari_chiusura(), oggetto, corpo)
    _memorizza_esito(anno, trimestre, msg)
    return ok, msg


def invia_notifica_riapertura(anno: int, trimestre: int) -> tuple[bool, str]:
    esito = controlla_chiusura(anno, trimestre)
    _, corpo_stato = componi_notifica(anno, trimestre, esito, chiusa=False)
    oggetto = f"Riapertura chiusura T{trimestre}/{anno}"
    corpo = (
        f"Il trimestre T{trimestre} {anno} è stato riaperto: i movimenti tornano modificabili "
        "fino a una nuova chiusura.\n\n"
        + corpo_stato
    )
    ok, msg = invia_email(destinatari_chiusura(), oggetto, corpo)
    _memorizza_esito(anno, trimestre, msg)
    return ok, msg
