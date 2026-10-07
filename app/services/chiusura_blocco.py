"""Impedisce modifiche ai periodi già chiusi."""

from datetime import date

from flask import flash

from app.models.movimento import trimestre_da_data
from app.services.chiusura_record import trimestre_chiuso


def messaggio_blocco(anno: int, giorno: date | None) -> str | None:
    if giorno is None:
        return None
    t = trimestre_da_data(giorno)
    if not trimestre_chiuso(anno, t):
        return None
    return (
        f"T{t} {anno} è chiuso: movimenti, buoni e allegati di quel periodo non si modificano. "
        "Per correggere, riapri la chiusura trimestre."
    )


def rifiuta_se_chiuso(anno: int, *giorni: date | None) -> bool:
    """True se almeno una data cade in un trimestre chiuso (e mostra l'avviso)."""
    for giorno in giorni:
        msg = messaggio_blocco(anno, giorno)
        if msg:
            flash(msg, "warning")
            return True
    return False
