from app.extensions import db


class FilialeBanca(db.Model):
    __tablename__ = "filiale_banca"

    id = db.Column(db.Integer, primary_key=True)
    denominazione = db.Column(db.String(200), nullable=False)
    indirizzo = db.Column(db.String(400), default="")
    attiva = db.Column(db.Boolean, nullable=False, default=True)
    ordinamento = db.Column(db.Integer, nullable=False, default=0)
