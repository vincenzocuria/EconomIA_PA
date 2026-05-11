from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Optional

from app.models.movimento import StatoMovimento


def _choices_stato():
    return [(e.value, e.value) for e in StatoMovimento]


class MovimentoForm(FlaskForm):
    data_movimento = DateField("Data movimento", validators=[DataRequired()])
    ora_movimento = TimeField("Ora (opzionale)", validators=[Optional()])
    tipo = SelectField("Tipo", choices=[], validators=[DataRequired()])
    importo = DecimalField("Importo", places=2, validators=[DataRequired()])
    causale = TextAreaField("Causale", validators=[Optional()])
    beneficiario_fornitore = StringField("Beneficiario / fornitore", validators=[Optional()])
    cf_piva = StringField("Codice fiscale / P.IVA", validators=[Optional()])
    buono_id = SelectField("Buono collegato", coerce=int, validators=[Optional()])
    num_documento_fiscale = StringField("Numero documento fiscale", validators=[Optional()])
    data_documento_fiscale = DateField("Data documento fiscale", validators=[Optional()])
    modalita_pagamento = StringField("Modalità pagamento", validators=[Optional()])
    filiale_id = SelectField("Filiale / sportello", coerce=int, validators=[Optional()])
    rif_ricevuta = StringField("Riferimento ricevuta operazione", validators=[Optional()])
    capitolo_riferimento = StringField("Capitolo / riferimento contabile", validators=[Optional()])
    note = TextAreaField("Note", validators=[Optional()])
    stato = SelectField("Stato", choices=_choices_stato(), validators=[DataRequired()])
    submit = SubmitField("Salva")


class StornoForm(FlaskForm):
    note = TextAreaField("Motivazione storno", validators=[DataRequired()])
    submit = SubmitField("Registra storno")
