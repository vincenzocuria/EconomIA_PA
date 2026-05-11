import enum

from app.extensions import db


class TipoAllegato(str, enum.Enum):
    scontrino = "scontrino"
    fattura = "fattura"
    ricevuta = "ricevuta"
    richiesta_ufficio = "richiesta_ufficio"
    autorizzazione = "autorizzazione"
    determina = "determina"
    verbale = "verbale"
    altro = "altro"


class Allegato(db.Model):
    __tablename__ = "allegato"

    id = db.Column(db.Integer, primary_key=True)
    filename_stored = db.Column(db.String(500), nullable=False)
    original_name = db.Column(db.String(500), default="")
    mime_type = db.Column(db.String(120), default="")
    sha256 = db.Column(db.String(64), default="", index=True)
    tipo_documento = db.Column(db.Enum(TipoAllegato), nullable=False, default=TipoAllegato.altro)
    movimento_id = db.Column(db.Integer, db.ForeignKey("movimento.id"), nullable=True)
    buono_id = db.Column(db.Integer, db.ForeignKey("buono_economale.id"), nullable=True)
    is_principale = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    movimento = db.relationship("Movimento", backref=db.backref("allegati", lazy="dynamic"))
    buono = db.relationship("BuonoEconomale", backref=db.backref("allegati", lazy="dynamic"))
