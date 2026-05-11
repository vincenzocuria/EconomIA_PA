from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class FilialeBancaForm(FlaskForm):
    denominazione = StringField("Denominazione", validators=[DataRequired(), Length(max=200)])
    indirizzo = TextAreaField("Indirizzo / note sportello", validators=[Optional(), Length(max=400)])
    attiva = BooleanField("Attiva (compare nelle nuove scelte)", default=True)
    ordinamento = IntegerField("Ordine elenco", default=0, validators=[Optional(), NumberRange(min=0, max=9999)])
    submit = SubmitField("Salva")
