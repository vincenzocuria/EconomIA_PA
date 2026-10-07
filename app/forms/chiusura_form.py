from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import DateField, DecimalField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional


_FILE = ["pdf", "png", "jpg", "jpeg", "webp"]


class FascicoloChiusuraForm(FlaskForm):
    saldo_estratto_iniziale = DecimalField(
        "Saldo estratto all'inizio del trimestre",
        places=2,
        validators=[Optional()],
    )
    saldo_estratto_finale = DecimalField(
        "Saldo estratto alla fine del trimestre",
        places=2,
        validators=[Optional()],
    )
    estratto = FileField(
        "Estratto conto del trimestre",
        validators=[Optional(), FileAllowed(_FILE, "PDF o immagini.")],
    )
    promemoria = FileField(
        "Promemoria del conto",
        validators=[Optional(), FileAllowed(_FILE, "PDF o immagini.")],
    )
    note = TextAreaField("Note", validators=[Optional()])
    submit = SubmitField("Salva fascicolo")


class VoceContoForm(FlaskForm):
    data_voce = DateField("Data", validators=[Optional()])
    descrizione = StringField("Descrizione", validators=[DataRequired(message="Indica la descrizione.")])
    importo = DecimalField(
        "Importo sul conto (+ accredito, − addebito)",
        places=2,
        validators=[DataRequired(message="Indica l'importo.")],
    )
    submit = SubmitField("Aggiungi voce estratto")


class QuietanzaForm(FlaskForm):
    file = FileField(
        "Quietanza firmata",
        validators=[FileRequired("Seleziona la quietanza firmata."), FileAllowed(_FILE, "PDF o immagini.")],
    )
    submit = SubmitField("Allega quietanza")
