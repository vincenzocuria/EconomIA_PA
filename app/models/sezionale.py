from app.extensions import db


class Sezionale(db.Model):
    __tablename__ = "sezionale"

    id = db.Column(db.Integer, primary_key=True)
    codice = db.Column(db.String(16), nullable=False, unique=True)
    descrizione = db.Column(db.String(200), default="")
    attiva = db.Column(db.Boolean, nullable=False, default=True)
    ordinamento = db.Column(db.Integer, nullable=False, default=0)
