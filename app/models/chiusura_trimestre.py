from app.extensions import db


class ChiusuraTrimestre(db.Model):
    """Fascicolo di chiusura di un trimestre (economo)."""

    __tablename__ = "chiusura_trimestre"

    id = db.Column(db.Integer, primary_key=True)
    anno = db.Column(db.Integer, nullable=False, index=True)
    trimestre = db.Column(db.Integer, nullable=False)
    stato = db.Column(db.String(20), nullable=False, default="aperta")
    note = db.Column(db.Text, default="")
    saldo_estratto_iniziale = db.Column(db.Numeric(12, 2), nullable=True)
    saldo_estratto_finale = db.Column(db.Numeric(12, 2), nullable=True)
    estratto_path = db.Column(db.String(500), default="")
    estratto_nome = db.Column(db.String(500), default="")
    estratto_sha = db.Column(db.String(64), default="")
    promemoria_path = db.Column(db.String(500), default="")
    promemoria_nome = db.Column(db.String(500), default="")
    promemoria_sha = db.Column(db.String(64), default="")
    prospetto_path = db.Column(db.String(500), default="")
    giornale_path = db.Column(db.String(500), default="")
    chiusa_il = db.Column(db.DateTime, nullable=True)
    chiusa_da_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    riaperta_il = db.Column(db.DateTime, nullable=True)
    ultima_notifica_il = db.Column(db.DateTime, nullable=True)
    ultima_notifica_esito = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    chiusa_da = db.relationship("User", foreign_keys=[chiusa_da_id])
    voci_conto = db.relationship(
        "VoceRiconciliazioneConto",
        back_populates="chiusura",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="VoceRiconciliazioneConto.id",
    )

    __table_args__ = (
        db.UniqueConstraint("anno", "trimestre", name="uq_chiusura_anno_trim"),
    )


class VoceRiconciliazioneConto(db.Model):
    """Voce dell'estratto che non passa dalla cassa (anticipazione, competenze, ritenute)."""

    __tablename__ = "voce_riconciliazione_conto"

    id = db.Column(db.Integer, primary_key=True)
    chiusura_id = db.Column(db.Integer, db.ForeignKey("chiusura_trimestre.id"), nullable=False, index=True)
    data_voce = db.Column(db.Date, nullable=True)
    descrizione = db.Column(db.String(300), nullable=False, default="")
    importo = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    chiusura = db.relationship("ChiusuraTrimestre", back_populates="voci_conto")
