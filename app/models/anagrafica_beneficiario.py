from app.extensions import db


class AnagraficaBeneficiario(db.Model):
    __tablename__ = "anagrafica_beneficiario"

    id = db.Column(db.Integer, primary_key=True)
    denominazione = db.Column(db.String(300), nullable=False)
    denominazione_norm = db.Column(db.String(300), nullable=False, unique=True, index=True)
    cf_piva = db.Column(db.String(32), default="")
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
