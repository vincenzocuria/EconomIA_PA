"""Alert operativi per dashboard."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.models.backup_run import BackupRun
from app.models.buono import BuonoEconomale, StatoBuono
from app.models.cassetto import SaldoAnnuale
from app.models.movimento import Movimento, StatoMovimento, TipoMovimento, trimestre_da_data
from app.models.verbale import VerbaleTrimestrale
from app.services.cassa import saldo_calcolato


def trimestre_corrente(d: date | None = None) -> tuple[int, int]:
    d = d or date.today()
    return d.year, trimestre_da_data(d)


def fine_trimestre(anno: int, trimestre: int) -> date:
    ultimo_mese = trimestre * 3
    if ultimo_mese == 3:
        return date(anno, 3, 31)
    if ultimo_mese == 6:
        return date(anno, 6, 30)
    if ultimo_mese == 9:
        return date(anno, 9, 30)
    return date(anno, 12, 31)


def prossima_scadenza_verbale(anno: int) -> date | None:
    """Data fine trimestre corrente (riferimento per verbale)."""
    y, t = trimestre_corrente()
    if anno != y:
        return date(anno, 12, 31)
    return fine_trimestre(anno, t)


def ultimo_backup() -> datetime | None:
    row = BackupRun.query.filter_by(ok=True).order_by(BackupRun.eseguito_il.desc()).first()
    return row.eseguito_il if row else None


def raccogli_alert(anno: int) -> list[dict]:
    out: list[dict] = []
    saldo_row = SaldoAnnuale.query.get(anno)
    ini = Decimal(str(saldo_row.saldo_iniziale)) if saldo_row else Decimal("0")
    saldo = saldo_calcolato(anno, ini)
    if saldo < 0:
        out.append({"livello": "danger", "testo": "Saldo di cassa negativo."})

    for m in Movimento.query.filter_by(anno=anno).filter(Movimento.stato != StatoMovimento.stornato):
        if m.tipo == TipoMovimento.uscita and m.allegati.count() == 0:
            out.append(
                {
                    "livello": "warning",
                    "testo": f"Movimento {m.numero_progressivo:04d} in uscita senza allegato.",
                }
            )
        if m.tipo == TipoMovimento.versamento_banca and m.allegati.count() == 0:
            out.append(
                {
                    "livello": "warning",
                    "testo": f"Movimento {m.numero_progressivo:04d} versamento in banca senza allegato (ricevuta).",
                }
            )
        if m.tipo == TipoMovimento.prelievo_banca and m.allegati.count() == 0:
            out.append(
                {
                    "livello": "warning",
                    "testo": f"Movimento {m.numero_progressivo:04d} prelievo banca senza allegato (ricevuta).",
                }
            )
        if m.tipo in (TipoMovimento.uscita, TipoMovimento.entrata):
            if not (m.num_documento_fiscale or "").strip() and m.tipo == TipoMovimento.uscita:
                out.append(
                    {
                        "livello": "secondary",
                        "testo": f"Movimento {m.numero_progressivo:04d}: documento fiscale non indicato.",
                    }
                )

    for b in BuonoEconomale.query.filter_by(anno=anno):
        if b.stato in (StatoBuono.autorizzato, StatoBuono.pagato):
            out.append(
                {
                    "livello": "info",
                    "testo": f"Buono {b.numero_progressivo:04d} non in stato chiuso.",
                }
            )

    for t in range(1, 5):
        oggi = date.today()
        if oggi.year == anno and t > trimestre_da_data(oggi):
            continue
        v = VerbaleTrimestrale.query.filter_by(anno=anno, trimestre=t).first()
        if v is None and (anno < oggi.year or (anno == oggi.year and fine_trimestre(anno, t) < oggi)):
            out.append(
                {
                    "livello": "warning",
                    "testo": f"Trimestre {t} {anno} senza verbale generato.",
                }
            )

    ultimo = ultimo_backup()
    now = datetime.now(timezone.utc)
    if ultimo is not None and ultimo.tzinfo is None:
        ultimo = ultimo.replace(tzinfo=timezone.utc)
    if ultimo is None or ultimo < now - timedelta(days=7):
        out.append(
            {
                "livello": "warning",
                "testo": "Backup non eseguito da più di 7 giorni (o mai eseguito).",
            }
        )

    verbali = VerbaleTrimestrale.query.filter_by(anno=anno).all()
    for m in Movimento.query.filter_by(anno=anno).all():
        for v in verbali:
            if m.trimestre != v.trimestre:
                continue
            if m.updated_at and v.generato_il and m.updated_at > v.generato_il:
                out.append(
                    {
                        "livello": "danger",
                        "testo": f"Movimento {m.numero_progressivo:04d} modificato dopo generazione verbale T{m.trimestre}.",
                    }
                )
                break

    seen = set()
    dedup = []
    for a in out:
        k = a["testo"]
        if k not in seen:
            seen.add(k)
            dedup.append(a)
    return dedup[:50]
