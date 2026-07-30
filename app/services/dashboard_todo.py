"""Voci aggregate «Cose da fare» per la dashboard."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from flask import url_for

from app.models.cassetto import SaldoAnnuale
from app.models.movimento import Movimento, StatoMovimento, TipoMovimento, trimestre_da_data
from app.models.verbale_verifica import VerbaleVerifica
from app.services.alerts import fine_trimestre, ultimo_backup
from app.services.buoni_kpi import kpi_buoni_anno
from app.services.cassa import saldo_cassa_calcolato, saldo_conto_calcolato


TIPI_SENZA_ALLEGATO = (
    TipoMovimento.uscita,
    TipoMovimento.versamento_banca,
    TipoMovimento.prelievo_banca,
)


def _voce(titolo: str, n: int, livello: str, url: str) -> dict:
    return {"titolo": titolo, "n": n, "livello": livello, "url": url}


def cose_da_fare(anno: int) -> list[dict]:
    out: list[dict] = []
    oggi = date.today()

    saldo_row = SaldoAnnuale.query.get(anno)
    ini_cassa = Decimal(str(saldo_row.saldo_iniziale)) if saldo_row else Decimal("0")
    ini_conto = (
        Decimal(str(getattr(saldo_row, "saldo_conto_iniziale", 0) or 0)) if saldo_row else Decimal("0")
    )
    saldo_cassa = saldo_cassa_calcolato(anno, ini_cassa)
    saldo_conto = saldo_conto_calcolato(anno, ini_conto)
    if saldo_cassa < 0:
        out.append(
            _voce(
                "Saldo di cassa negativo",
                1,
                "danger",
                url_for("impostazioni.cassa", anno=anno),
            )
        )
    if saldo_conto < 0:
        out.append(
            _voce(
                "Saldo di conto economale negativo",
                1,
                "warning",
                url_for("impostazioni.cassa", anno=anno),
            )
        )

    n_giust = (
        Movimento.query.filter_by(anno=anno, da_giustificare=True)
        .filter(Movimento.stato != StatoMovimento.stornato)
        .count()
    )
    if n_giust:
        out.append(
            _voce(
                "Movimenti da giustificare",
                n_giust,
                "warning",
                url_for("movimenti.lista", anno=anno, da_giustificare=1),
            )
        )

    n_buoni = kpi_buoni_anno(anno)["n_da_chiudere"]
    if n_buoni:
        out.append(
            _voce(
                "Buoni da chiudere (autorizzati/pagati)",
                n_buoni,
                "info",
                url_for("buoni.lista", anno=anno, rapido="da_chiudere"),
            )
        )

    n_allegati = 0
    for m in (
        Movimento.query.filter_by(anno=anno)
        .filter(
            Movimento.stato != StatoMovimento.stornato,
            Movimento.tipo.in_(TIPI_SENZA_ALLEGATO),
        )
        .all()
    ):
        if m.allegati.count() == 0:
            n_allegati += 1
    if n_allegati:
        out.append(
            _voce(
                "Uscite/banca senza allegato",
                n_allegati,
                "warning",
                url_for("movimenti.lista", anno=anno),
            )
        )

    trim_mancanti = 0
    for t in range(1, 5):
        if oggi.year == anno and t > trimestre_da_data(oggi):
            continue
        trim_chiuso = anno < oggi.year or (anno == oggi.year and fine_trimestre(anno, t) < oggi)
        if not trim_chiuso:
            continue
        if VerbaleVerifica.query.filter_by(anno=anno, trimestre=t).first() is None:
            trim_mancanti += 1
    if trim_mancanti:
        out.append(
            _voce(
                "Verbali ufficiali mancanti (trimestri chiusi)",
                trim_mancanti,
                "warning",
                url_for("verbali.lista", anno=anno),
            )
        )

    ultimo = ultimo_backup()
    now = datetime.now(timezone.utc)
    if ultimo is not None and ultimo.tzinfo is None:
        ultimo = ultimo.replace(tzinfo=timezone.utc)
    if ultimo is None or ultimo < now - timedelta(days=7):
        out.append(
            _voce(
                "Backup non eseguito da più di 7 giorni (o mai)",
                1,
                "warning",
                url_for("backup_export.index", anno=anno),
            )
        )

    return out
