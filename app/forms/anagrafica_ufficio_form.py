from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class AnagraficaUfficioForm(FlaskForm):
    denominazione = StringField("Ufficio", validators=[DataRequired(), Length(max=300)])
    responsabile = StringField("Responsabile", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Salva")
