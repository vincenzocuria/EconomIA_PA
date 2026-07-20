from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


class VerbaleVerificaForm(FlaskForm):
    numero = IntegerField("Numero verbale", validators=[DataRequired(), NumberRange(min=1)])
    data_verbale = DateField("Data verbale", validators=[DataRequired()])
    trimestre = SelectField(
        "Trimestre",
        coerce=int,
        choices=[(1, "T1"), (2, "T2"), (3, "T3"), (4, "T4")],
        validators=[DataRequired()],
    )
    oggetto = StringField("Oggetto", validators=[DataRequired()])
    note = TextAreaField("Note", validators=[Optional()])
    file = FileField(
        "PDF firmato",
        validators=[
            DataRequired(),
            FileAllowed(["pdf"], "Solo file PDF."),
        ],
    )
    submit = SubmitField("Salva verbale")
