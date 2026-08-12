from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import DateField, DecimalField, StringField, SubmitField, TextAreaField
from wtforms.validators import Optional

class EnteForm(FlaskForm):
    denominazione = StringField("Denominazione")
    codice_fiscale_ente = StringField("Codice fiscale / P.IVA ente")
    codice_istat = StringField("Codice ISTAT")
    indirizzo = StringField("Indirizzo")
    cap = StringField("CAP")
    comune = StringField("Comune")
    provincia = StringField("Provincia")
    pec = StringField("PEC")
    email = StringField("Email")
    telefono = StringField("Telefono")
    note_legali = TextAreaField("Note legali / richiami normativi sui documenti")
    logo = FileField(
        "Logo (PNG/JPG/WebP)",
        validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "webp"], "Solo immagini.")],
    )
    submit = SubmitField("Salva dati ente")


class EconomoForm(FlaskForm):
    cognome = StringField("Cognome")
    nome = StringField("Nome")
    codice_fiscale = StringField("Codice fiscale")
    qualifica = StringField("Qualifica")
    incarico_dal = DateField("Incarico dal", validators=[Optional()])
    delibera_nomina = StringField("Riferimento delibera di nomina")
    telefono = StringField("Telefono")
    email = StringField("Email")
    note = TextAreaField("Note")
    determina = FileField(
        "Determina (PDF/immagine)",
        validators=[Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg", "webp"], "PDF o immagini.")],
    )
    regolamento = FileField(
        "Regolamento comunale (PDF/immagine)",
        validators=[Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg", "webp"], "PDF o immagini.")],
    )
    submit = SubmitField("Salva dati economo")


class SaldoAnnoForm(FlaskForm):
    saldo_iniziale = DecimalField("Saldo iniziale cassa (contanti)", places=2)
    saldo_conto_iniziale = DecimalField("Saldo iniziale conto (estratto)", places=2)
    note = TextAreaField("Note")
    submit = SubmitField("Aggiorna saldi annuali")
