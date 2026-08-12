# EconomIA_PA (EcoGest Comune)

Registro locale di supporto per la **cassa economale** comunale: movimenti, buoni, allegati, verbali e pre-rendicontazione.

Non sostituisce protocollo, contabilità ufficiale né conservazione digitale dell’ente.

## Funzioni principali

- **Dashboard** con saldi cassa/conto, ultimi movimenti banca e elenco **Cose da fare** (giustificativi, allegati mancanti, buoni da chiudere, **buoni da far firmare / ricaricare firmati**, verbali, backup)
- **Movimenti** (entrate, uscite, banca, storni) con allegati e sezionali
- **Buoni economali**: scheda PDF + **modulo rimborso Word** (una pagina) da far firmare e ricaricare; anagrafiche richiedenti/uffici/responsabili
- **Allegati**, **verbali** ufficiali di verifica, **impostazioni** ente/economo/cassa, backup/export

## Requisiti

- Python 3.11+ consigliato
- Dipendenze in `requirements.txt`

## Avvio rapido

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Apri [http://127.0.0.1:5050](http://127.0.0.1:5050) (porta configurabile con `PORT` nel `.env`).

Su Windows puoi anche usare `scripts\avvia_ecogest.bat` (opzionale: collegamento desktop con `scripts\crea_collegamento_desktop.ps1`).

### Accesso iniziale

Al primo avvio viene creato l’utente da `.env`:

- `ECONOMIA_PA_ADMIN_USER` (default `economo`)
- `ECONOMIA_PA_ADMIN_PASSWORD` (se assente, password temporanea `economo` — da cambiare)

Per riallineare le credenziali su un DB già esistente: `ECONOMIA_PA_ADMIN_SYNC=1`, riavvio, poi rimuovere il flag.

I dati SQLite e gli upload restano in `instance/` (non versionata).

## Note operative

- Il pulsante **Modulo** genera il DOCX di richiesta rimborso; **PDF** è lo scheda-riepilogo del buono.
- Le anagrafiche normalizzano i nomi e supportano ricerca per token (anche con apostrofo / ordine nome-cognome diverso).
- Gli allegati ammessi sono PDF e immagini.
