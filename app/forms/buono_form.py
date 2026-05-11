from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

from app.models.buono import StatoBuono


class BuonoForm(FlaskForm):
    data_buono = DateField("Data", validators=[DataRequired()])
    richiedente = StringField("Richiedente", validators=[Optional()])
    ufficio_richiedente = StringField("Ufficio richiedente", validators=[Optional()])
    causale = TextAreaField("Causale", validators=[Optional()])
    importo_autorizzato = DecimalField("Importo autorizzato", places=2, validators=[DataRequired()])
    importo_speso = DecimalField("Importo speso", places=2, validators=[Optional()], default=0)
    beneficiario = StringField("Beneficiario", validators=[Optional()])
    stato = SelectField(
        "Stato",
        choices=[(e.value, e.value) for e in StatoBuono],
        validators=[DataRequired()],
    )
    note = TextAreaField("Note", validators=[Optional()])
    submit = SubmitField("Salva")
