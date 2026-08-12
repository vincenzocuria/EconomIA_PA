from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class AnagraficaRichiedenteForm(FlaskForm):
    nome = StringField("Nome richiedente", validators=[DataRequired(), Length(max=300)])
    ufficio_default = StringField("Ufficio associato", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Salva")
