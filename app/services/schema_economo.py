"""Patch tabella economo_settings: path determina e regolamento."""
from sqlalchemy import inspect, text

from app.extensions import db


def applica_schema_economo() -> None:
    engine = db.engine
    insp = inspect(engine)
    if not insp.has_table("economo_settings"):
        return
    names = {c["name"] for c in insp.get_columns("economo_settings")}
    for col in ("determina_path", "regolamento_path"):
        if col not in names:
            db.session.execute(
                text(f"ALTER TABLE economo_settings ADD COLUMN {col} VARCHAR(500) DEFAULT ''")
            )
    db.session.commit()
