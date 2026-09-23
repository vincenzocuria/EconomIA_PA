"""Ricompatta i progressivi per anno e sezionale e rinomina gli allegati collegati."""

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from werkzeug.utils import secure_filename

from app.config import INSTANCE_DIR
from app.extensions import db
from app.models.allegato import Allegato
from app.models.buono import BuonoEconomale
from app.models.movimento import Movimento
from app.services.upload_allegato import nome_file_allegato


def _compatta(righe: list, data_attr: str) -> None:
    """Assegna 1..n per (anno, sezionale), in ordine di data poi id."""
    gruppi: dict[tuple, list] = defaultdict(list)
    for riga in righe:
        gruppi[(riga.anno, riga.sezionale_id)].append(riga)
    for gruppo in gruppi.values():
        gruppo.sort(key=lambda r: (getattr(r, data_attr), r.id))
        attesi = list(range(1, len(gruppo) + 1))
        if [r.numero_progressivo for r in gruppo] == attesi:
            continue
        for riga in gruppo:
            riga.numero_progressivo = -int(riga.id)
        db.session.flush()
        for indice, riga in enumerate(gruppo, start=1):
            riga.numero_progressivo = indice
        db.session.flush()


def _importo(val) -> str:
    return f"{Decimal(val or 0):.2f}"


def _nome_allegato(allegato: Allegato) -> str | None:
    """Nuovo nome file con il progressivo già riassegnato. None se non è MOV/BUO."""
    attuale = Path(allegato.filename_stored).name
    ext = Path(attuale).suffix.lstrip(".").lower()
    if not ext:
        return None
    if allegato.movimento_id:
        mov = allegato.movimento
        if mov is None:
            return None
        return nome_file_allegato(
            mov.data_movimento,
            "MOV",
            mov.numero_progressivo,
            allegato.tipo_documento,
            mov.beneficiario_fornitore or "",
            _importo(mov.importo),
            ext,
        )
    if allegato.buono_id:
        buono = allegato.buono
        if buono is None:
            return None
        return nome_file_allegato(
            buono.data_buono,
            "BUO",
            buono.numero_progressivo,
            allegato.tipo_documento,
            buono.richiedente or buono.beneficiario or "",
            _importo(buono.importo_speso or buono.importo_autorizzato),
            ext,
        )
    return None


def _ripristina(mosse: list[tuple[Path, Path]]) -> None:
    """Riporta i file alla posizione originale. mosse è (dove_è_ora, origine)."""
    for attuale, origine in reversed(mosse):
        if attuale.is_file() and not origine.exists():
            attuale.rename(origine)


def _rinomina_allegati() -> tuple[list[str], list[tuple[Path, Path]]]:
    """Due fasi: nome temporaneo, poi nome definitivo. Ritorna diario e mosse da annullare."""
    piani: list[tuple[Allegato, Path, Path, str]] = []
    for allegato in Allegato.query.order_by(Allegato.id).all():
        nuovo = _nome_allegato(allegato)
        if not nuovo:
            continue
        sicuro = secure_filename(nuovo)
        src = INSTANCE_DIR / allegato.filename_stored
        dst = src.parent / sicuro
        if src.resolve() == dst.resolve():
            continue
        piani.append((allegato, src, dst, sicuro))

    sorgenti = {src for _a, src, _d, _s in piani}
    for _allegato, src, dst, _sicuro in piani:
        if not src.is_file():
            raise FileNotFoundError(f"Allegato mancante su disco: {src}")
        if dst.exists() and dst not in sorgenti:
            raise FileExistsError(f"Destinazione già presente: {dst}")
    destinazioni = [dst for _a, _s, dst, _n in piani]
    if len(destinazioni) != len(set(destinazioni)):
        raise FileExistsError("Due allegati finirebbero sullo stesso nome file.")

    mosse: list[tuple[Path, Path]] = []
    try:
        for _allegato, src, _dst, _sicuro in piani:
            tmp = src.with_name(src.name + ".rinumera")
            if tmp.exists():
                raise FileExistsError(f"Temporaneo già presente: {tmp}")
            src.rename(tmp)
            mosse.append((tmp, src))
        log: list[str] = []
        for allegato, src, dst, sicuro in piani:
            tmp = src.with_name(src.name + ".rinumera")
            tmp.rename(dst)
            mosse.append((dst, src))
            mosse.remove((tmp, src))
            rel = dst.relative_to(INSTANCE_DIR)
            allegato.filename_stored = str(rel)
            log.append(f"file {src.name} -> {sicuro}")
        return log, mosse
    except Exception:
        _ripristina(mosse)
        raise


def rinumera_progressivi() -> list[str]:
    """Ricompatta movimenti e buoni, rinomina gli allegati, fa commit."""
    mosse: list[tuple[Path, Path]] = []
    try:
        _compatta(Movimento.query.all(), "data_movimento")
        _compatta(BuonoEconomale.query.all(), "data_buono")
        log, mosse = _rinomina_allegati()
        db.session.commit()
        return log
    except Exception:
        db.session.rollback()
        _ripristina(mosse)
        raise
