from app.extensions import db


class SaldoAnnuale(db.Model):
    """Saldi iniziali per anno: cassa (contanti) e conto economale."""

    __tablename__ = "saldo_annuale"

    anno = db.Column(db.Integer, primary_key=True)
    saldo_iniziale = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    saldo_conto_iniziale = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    note = db.Column(db.Text, default="")
