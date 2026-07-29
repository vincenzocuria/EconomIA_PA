import enum
from datetime import date

from app.extensions import db


class TipoMovimento(str, enum.Enum):
    entrata = "entrata"
    uscita = "uscita"
    reintegro = "reintegro"
    prelievo_banca = "prelievo_banca"
    versamento_banca = "versamento_banca"
    rettifica = "rettifica"
    storno = "storno"


class StatoMovimento(str, enum.Enum):
    registrato = "registrato"
    rendicontato = "rendicontato"
    stornato = "stornato"
    rettificato = "rettificato"


def trimestre_da_data(d: date) -> int:
    return (d.month - 1) // 3 + 1


class Movimento(db.Model):
    __tablename__ = "movimento"

    id = db.Column(db.Integer, primary_key=True)
    anno = db.Column(db.Integer, nullable=False, index=True)
    numero_progressivo = db.Column(db.Integer, nullable=False)
    data_movimento = db.Column(db.Date, nullable=False, index=True)
    ora_movimento = db.Column(db.Time, nullable=True)
    tipo = db.Column(db.Enum(TipoMovimento), nullable=False)
    importo = db.Column(db.Numeric(12, 2), nullable=False)
    causale = db.Column(db.Text, default="")
    beneficiario_fornitore = db.Column(db.String(300), default="")
    cf_piva = db.Column(db.String(32), default="")
    buono_id = db.Column(db.Integer, db.ForeignKey("buono_economale.id"), nullable=True)
    num_documento_fiscale = db.Column(db.String(120), default="")
    data_documento_fiscale = db.Column(db.Date, nullable=True)
    modalita_pagamento = db.Column(db.String(120), default="")
    filiale_id = db.Column(db.Integer, db.ForeignKey("filiale_banca.id"), nullable=True)
    filiale_banca = db.Column(db.String(200), default="")
    rif_ricevuta = db.Column(db.String(120), default="")
    capitolo_riferimento = db.Column(db.String(200), default="")
    note = db.Column(db.Text, default="")
    da_giustificare = db.Column(db.Boolean, nullable=False, default=False, index=True)
    stato = db.Column(db.Enum(StatoMovimento), nullable=False, default=StatoMovimento.registrato)
    trimestre = db.Column(db.Integer, nullable=False, default=1)
    movimento_collegato_id = db.Column(db.Integer, db.ForeignKey("movimento.id"), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    buono = db.relationship(
        "BuonoEconomale",
        foreign_keys=[buono_id],
        back_populates="movimenti",
    )
    movimento_collegato = db.relationship(
        "Movimento",
        remote_side=[id],
        foreign_keys=[movimento_collegato_id],
    )
    creato_da = db.relationship("User", foreign_keys=[created_by_id])
    filiale = db.relationship(
        "FilialeBanca",
        foreign_keys=[filiale_id],
        backref=db.backref("movimenti", lazy="dynamic"),
        lazy="joined",
    )

    __table_args__ = (
        db.UniqueConstraint("anno", "numero_progressivo", name="uq_movimento_anno_num"),
    )
