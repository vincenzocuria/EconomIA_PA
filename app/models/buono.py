import enum

from app.extensions import db


class StatoBuono(str, enum.Enum):
    bozza = "bozza"
    autorizzato = "autorizzato"
    pagato = "pagato"
    chiuso = "chiuso"
    annullato = "annullato"


class BuonoEconomale(db.Model):
    __tablename__ = "buono_economale"

    id = db.Column(db.Integer, primary_key=True)
    anno = db.Column(db.Integer, nullable=False, index=True)
    sezionale_id = db.Column(db.Integer, db.ForeignKey("sezionale.id"), nullable=True, index=True)
    numero_progressivo = db.Column(db.Integer, nullable=False)
    data_buono = db.Column(db.Date, nullable=False)
    richiedente = db.Column(db.String(300), default="")
    ufficio_richiedente = db.Column(db.String(300), default="")
    causale = db.Column(db.Text, default="")
    importo_autorizzato = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    importo_speso = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    beneficiario = db.Column(db.String(300), default="")
    stato = db.Column(db.Enum(StatoBuono), nullable=False, default=StatoBuono.bozza)
    note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    sezionale = db.relationship(
        "Sezionale",
        foreign_keys=[sezionale_id],
        lazy="joined",
    )
    movimenti = db.relationship(
        "Movimento",
        foreign_keys="Movimento.buono_id",
        back_populates="buono",
        lazy="dynamic",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "anno",
            "sezionale_id",
            "numero_progressivo",
            name="uq_buono_anno_sez_num",
        ),
    )
