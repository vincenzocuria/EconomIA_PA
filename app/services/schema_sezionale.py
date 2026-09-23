"""Tabella sezionali, colonna su movimento/buono, seed GEN/RIM/BAN."""

import re

from sqlalchemy import inspect, text

from app.extensions import db

# Vincolo di tabella SQLite: DROP INDEX non lo rimuove (è un autoindex).
_UNIQUE_ANNO_NUMERO = re.compile(
    r"CONSTRAINT\s+\"?[A-Za-z0-9_]+\"?\s+UNIQUE\s*\(\s*anno\s*,\s*numero_progressivo\s*\)\s*,?",
    re.IGNORECASE,
)

SEED = (
    ("GEN", "Spese generali", 0),
    ("RIM", "Rimborsi dipendenti", 1),
    ("BAN", "Prelievi / versamenti banca", 2),
)


def _aggiungi_colonna_sezionale(tabella: str) -> None:
    insp = inspect(db.engine)
    if not insp.has_table(tabella):
        return
    cols = {c["name"] for c in insp.get_columns(tabella)}
    if "sezionale_id" not in cols:
        db.session.execute(text(f"ALTER TABLE {tabella} ADD COLUMN sezionale_id INTEGER"))
        db.session.commit()


def _sql_crea_tabella(tabella: str) -> str | None:
    return db.session.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": tabella},
    ).scalar()


def _sql_indici(tabella: str) -> list[str]:
    rows = db.session.execute(
        text(
            "SELECT sql FROM sqlite_master "
            "WHERE type='index' AND tbl_name=:n AND sql IS NOT NULL"
        ),
        {"n": tabella},
    ).fetchall()
    return [r[0] for r in rows]


def _togli_unique_anno_numero(tabella: str) -> None:
    """Ricrea la tabella senza UNIQUE(anno, numero_progressivo), dati invariati."""
    sql = _sql_crea_tabella(tabella)
    if not sql or not _UNIQUE_ANNO_NUMERO.search(sql):
        return
    indici = _sql_indici(tabella)
    nuovo_sql = _UNIQUE_ANNO_NUMERO.sub("", sql)
    nuovo_sql = re.sub(r",\s*,", ",", nuovo_sql)
    nuovo_sql = re.sub(r",\s*\)", ")", nuovo_sql)
    tmp = f"{tabella}__nuovo"
    if not nuovo_sql.startswith(f"CREATE TABLE {tabella}"):
        raise RuntimeError(f"CREATE TABLE inatteso per {tabella}")
    nuovo_sql = nuovo_sql.replace(f"CREATE TABLE {tabella}", f"CREATE TABLE {tmp}", 1)
    cols = [c["name"] for c in inspect(db.engine).get_columns(tabella)]
    col_sql = ", ".join(f'"{c}"' for c in cols)

    db.session.commit()
    raw = db.engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute("PRAGMA foreign_keys=OFF")
        cur.execute("BEGIN")
        cur.execute(nuovo_sql)
        cur.execute(
            f'INSERT INTO "{tmp}" ({col_sql}) SELECT {col_sql} FROM "{tabella}"'
        )
        cur.execute(f'DROP TABLE "{tabella}"')
        cur.execute(f'ALTER TABLE "{tmp}" RENAME TO "{tabella}"')
        for idx_sql in indici:
            cur.execute(idx_sql)
        raw.commit()
        cur.execute("PRAGMA foreign_keys=ON")
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()
    db.session.expire_all()


def _rigenera_unicita(tabella: str, vecchio: str, nuovo: str) -> None:
    """SQLite: unicità su anno+sezionale+numero, non più solo anno+numero."""
    insp = inspect(db.engine)
    if not insp.has_table(tabella):
        return
    _togli_unique_anno_numero(tabella)
    db.session.execute(text(f"DROP INDEX IF EXISTS {vecchio}"))
    db.session.commit()
    db.session.execute(
        text(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {nuovo} "
            f"ON {tabella} (anno, sezionale_id, numero_progressivo)"
        )
    )
    db.session.commit()


def _seed_e_backfill() -> None:
    from app.models.buono import BuonoEconomale
    from app.models.movimento import Movimento, TipoMovimento
    from app.models.sezionale import Sezionale

    for codice, desc, ord_ in SEED:
        if Sezionale.query.filter_by(codice=codice).first() is None:
            db.session.add(
                Sezionale(
                    codice=codice,
                    descrizione=desc,
                    attiva=True,
                    ordinamento=ord_,
                )
            )
    db.session.commit()

    gen = Sezionale.query.filter_by(codice="GEN").first()
    ban = Sezionale.query.filter_by(codice="BAN").first()
    if ban is not None:
        Movimento.query.filter(
            Movimento.sezionale_id.is_(None),
            Movimento.tipo.in_(
                (TipoMovimento.prelievo_banca, TipoMovimento.versamento_banca)
            ),
        ).update(
            {Movimento.sezionale_id: ban.id},
            synchronize_session=False,
        )
    if gen is not None:
        Movimento.query.filter(Movimento.sezionale_id.is_(None)).update(
            {Movimento.sezionale_id: gen.id},
            synchronize_session=False,
        )
        BuonoEconomale.query.filter(BuonoEconomale.sezionale_id.is_(None)).update(
            {BuonoEconomale.sezionale_id: gen.id},
            synchronize_session=False,
        )
    db.session.commit()


def applica_schema_sezionale() -> None:
    from app.models.sezionale import Sezionale

    engine = db.engine
    insp = inspect(engine)
    if not insp.has_table("sezionale"):
        Sezionale.__table__.create(bind=engine)

    _aggiungi_colonna_sezionale("movimento")
    _aggiungi_colonna_sezionale("buono_economale")
    _seed_e_backfill()
    _rigenera_unicita("movimento", "uq_movimento_anno_num", "uq_movimento_anno_sez_num")
    _rigenera_unicita("buono_economale", "uq_buono_anno_num", "uq_buono_anno_sez_num")
