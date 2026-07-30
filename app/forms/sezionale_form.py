from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp


class SezionaleForm(FlaskForm):
    codice = StringField(
        "Codice",
        validators=[
            DataRequired(),
            Length(min=1, max=16),
            Regexp(r"^[A-Za-z0-9_-]+$", message="Solo lettere, numeri, _ o -"),
        ],
    )
    descrizione = StringField("Descrizione", validators=[Optional(), Length(max=200)])
    attiva = BooleanField("Attivo", default=True)
    ordinamento = IntegerField(
        "Ordine elenco",
        default=0,
        validators=[Optional(), NumberRange(min=0, max=9999)],
    )
    submit = SubmitField("Salva")
