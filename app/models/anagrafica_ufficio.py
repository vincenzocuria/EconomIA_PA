from app.extensions import db


class AnagraficaUfficio(db.Model):
    __tablename__ = "anagrafica_ufficio"

    id = db.Column(db.Integer, primary_key=True)
    denominazione = db.Column(db.String(300), nullable=False)
    denominazione_norm = db.Column(db.String(300), nullable=False, unique=True, index=True)
    responsabile = db.Column(db.String(300), default="")
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
