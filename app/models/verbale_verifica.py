from app.extensions import db


class VerbaleVerifica(db.Model):
    """Verbale ufficiale di verifica di cassa economale (PDF firmato)."""

    __tablename__ = "verbale_verifica"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False)
    data_verbale = db.Column(db.Date, nullable=False)
    anno = db.Column(db.Integer, nullable=False, index=True)
    trimestre = db.Column(db.Integer, nullable=False)
    oggetto = db.Column(db.String(500), default="")
    note = db.Column(db.Text, default="")
    filename_stored = db.Column(db.String(500), nullable=False)
    original_name = db.Column(db.String(500), default="")
    mime_type = db.Column(db.String(120), default="application/pdf")
    sha256 = db.Column(db.String(64), default="", index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("anno", "trimestre", name="uq_verbale_verifica_anno_trim"),
    )
