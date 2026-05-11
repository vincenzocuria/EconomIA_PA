"""Rimuove il database SQLite locale e i file WAL/SHM. Chiudi Flask prima di eseguire."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "instance" / "economia_pa.sqlite3"
EXTRA_SUFFIXES = ("-wal", "-shm")


def main() -> int:
    paths = [DB] + [DB.parent / f"{DB.name}{s}" for s in EXTRA_SUFFIXES]
    removed = 0
    for p in paths:
        if not p.is_file():
            continue
        try:
            p.unlink()
            print("Rimosso:", p)
            removed += 1
        except OSError as e:
            print("ERRORE:", p, "→", e, file=sys.stderr)
            print("Chiudi il server Flask (Ctrl+C nel terminale) e rilancia questo script.", file=sys.stderr)
            return 1
    if removed == 0:
        print("Nessun file da rimuovere (già assente?):", DB)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
