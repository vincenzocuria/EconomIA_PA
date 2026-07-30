from app.extensions import db


class AnagraficaRichiedente(db.Model):
    __tablename__ = "anagrafica_richiedente"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(300), nullable=False)
    nome_norm = db.Column(db.String(300), nullable=False, unique=True, index=True)
    ufficio_default = db.Column(db.String(300), default="")
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
