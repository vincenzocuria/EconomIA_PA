"""Colonna anno su allegato e backfill da movimento/buono (SQLite)."""

from sqlalchemy import inspect, text

from app.extensions import db


def applica_schema_allegato() -> None:
    engine = db.engine
    insp = inspect(engine)
    if not insp.has_table("allegato"):
        return
    names = {c["name"] for c in insp.get_columns("allegato")}
    if "anno" not in names:
        db.session.execute(text("ALTER TABLE allegato ADD COLUMN anno INTEGER"))
        db.session.commit()
    db.session.execute(
        text(
            """
            UPDATE allegato
            SET anno = (
                SELECT movimento.anno FROM movimento
                WHERE movimento.id = allegato.movimento_id
            )
            WHERE movimento_id IS NOT NULL AND anno IS NULL
            """
        )
    )
    db.session.execute(
        text(
            """
            UPDATE allegato
            SET anno = (
                SELECT buono_economale.anno FROM buono_economale
                WHERE buono_economale.id = allegato.buono_id
            )
            WHERE buono_id IS NOT NULL AND anno IS NULL
            """
        )
    )
    db.session.commit()
