"""Tabella sezionali, colonna su movimento/buono, seed GEN/RIM/BAN."""

from sqlalchemy import inspect, text

from app.extensions import db

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


def _rigenera_unicita(tabella: str, vecchio: str, nuovo: str) -> None:
    """SQLite: sostituisce indice UNIQUE anno+numero con anno+sezionale+numero."""
    insp = inspect(db.engine)
    if not insp.has_table(tabella):
        return
    indexes = {ix["name"]: ix for ix in insp.get_indexes(tabella)}
    if vecchio in indexes:
        db.session.execute(text(f"DROP INDEX IF EXISTS {vecchio}"))
        db.session.commit()
    # Anche nome automatico SQLite a volte diverso; cerca per colonne
    insp = inspect(db.engine)
    for ix in insp.get_indexes(tabella):
        cols = list(ix.get("column_names") or [])
        if ix.get("unique") and cols == ["anno", "numero_progressivo"]:
            db.session.execute(text(f'DROP INDEX IF EXISTS "{ix["name"]}"'))
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
    from app.models.movimento import Movimento
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
    if gen is None:
        return
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
