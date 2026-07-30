from app.models.allegato import Allegato
from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
from app.models.anagrafica_richiedente import AnagraficaRichiedente
from app.models.anagrafica_ufficio import AnagraficaUfficio
from app.models.audit import AuditLog
from app.models.backup_run import BackupRun
from app.models.buono import BuonoEconomale
from app.models.cassetto import SaldoAnnuale
from app.models.economo import EconomoSettings
from app.models.ente import EnteSettings
from app.models.filiale_banca import FilialeBanca
from app.models.movimento import Movimento
from app.models.sezionale import Sezionale
from app.models.user import User
from app.models.verbale import VerbaleTrimestrale
from app.models.verbale_verifica import VerbaleVerifica

__all__ = [
    "Allegato",
    "AnagraficaBeneficiario",
    "AnagraficaRichiedente",
    "AnagraficaUfficio",
    "AuditLog",
    "BackupRun",
    "BuonoEconomale",
    "EconomoSettings",
    "EnteSettings",
    "FilialeBanca",
    "Movimento",
    "SaldoAnnuale",
    "Sezionale",
    "User",
    "VerbaleTrimestrale",
    "VerbaleVerifica",
]
