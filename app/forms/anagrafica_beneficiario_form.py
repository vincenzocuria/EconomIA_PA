from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class AnagraficaBeneficiarioForm(FlaskForm):
    denominazione = StringField("Denominazione", validators=[DataRequired(), Length(max=300)])
    cf_piva = StringField("Codice fiscale / P.IVA", validators=[Optional(), Length(max=32)])
    submit = SubmitField("Salva")
