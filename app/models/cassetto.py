from app.extensions import db


class SaldoAnnuale(db.Model):
    """Saldo iniziale per anno contabile economale."""

    __tablename__ = "saldo_annuale"

    anno = db.Column(db.Integer, primary_key=True)
    saldo_iniziale = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    note = db.Column(db.Text, default="")
