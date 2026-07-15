from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

from app.services.allegato_tipi import scelte_tipo_allegato


class AllegatoForm(FlaskForm):
    tipo_documento = SelectField(
        "Tipo documento",
        choices=scelte_tipo_allegato(),
        validators=[DataRequired()],
    )
    movimento_id = SelectField("Movimento", coerce=int, validators=[Optional()])
    buono_id = SelectField("Buono", coerce=int, validators=[Optional()])
    is_principale = BooleanField("Documento principale")
    comprimi = BooleanField("Comprimi immagine (JPEG)")
    file = FileField(
        "File",
        validators=[
            DataRequired(),
            FileAllowed(["pdf", "jpg", "jpeg", "png", "webp"], "Solo PDF o immagini consentite."),
        ],
    )
    submit = SubmitField("Carica")
