from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    DateField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, NumberRange, Optional

from app.models.buono import StatoBuono


class BuonoForm(FlaskForm):
    sezionale_id = SelectField("Sezionale", coerce=int, validators=[DataRequired()])
    numero_progressivo = IntegerField(
        "Numero",
        validators=[DataRequired(), NumberRange(min=1, max=999999)],
    )
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
    allegato_firmato = FileField(
        "Modulo firmato (PDF o immagine)",
        validators=[
            Optional(),
            FileAllowed(["pdf", "jpg", "jpeg", "png", "webp"], "Solo PDF o immagini."),
        ],
    )
    submit = SubmitField("Salva")
