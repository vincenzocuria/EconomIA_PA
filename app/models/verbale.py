from app.extensions import db


class VerbaleTrimestrale(db.Model):
    __tablename__ = "verbale_trimestrale"

    id = db.Column(db.Integer, primary_key=True)
    anno = db.Column(db.Integer, nullable=False, index=True)
    trimestre = db.Column(db.Integer, nullable=False)
    generato_il = db.Column(db.DateTime, server_default=db.func.now())
    percorso_pdf = db.Column(db.String(500), default="")

    __table_args__ = (
        db.UniqueConstraint("anno", "trimestre", name="uq_verbale_anno_trim"),
    )
