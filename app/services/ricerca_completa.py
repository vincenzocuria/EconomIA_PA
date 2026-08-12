"""Ricerca testuale completa: token in qualsiasi ordine, apostrofi tollerati."""

from sqlalchemy import and_, or_

from app.services.anagrafiche_testo import pulisci_testo, unifica_apostrofi


def _escape_like(valore: str) -> str:
    return (
        (valore or "")
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def token_ricerca(q: str | None, max_len: int = 120) -> list[str]:
    """Token di ricerca normalizzati (ordine indipendente)."""
    testo = pulisci_testo(q, max_len=max_len)
    if not testo:
        return []
    grezzo = unifica_apostrofi(testo).casefold()
    return [t for t in grezzo.split() if t]


def varianti_token(token: str) -> list[str]:
    """
    Varianti LIKE per un token.
    Es. d'amico → d'amico | damico | d%amico (tolera apostrofo assente/diverso).
    """
    base = unifica_apostrofi(token or "").casefold().strip()
    if not base:
        return []
    out: list[str] = []
    esc = _escape_like(base)
    out.append(esc)
    senza = _escape_like(base.replace("'", ""))
    if senza and senza not in out:
        out.append(senza)
    if "'" in base:
        con_jolly = esc.replace("'", "%")
        if con_jolly not in out:
            out.append(con_jolly)
    return out


def condizione_ricerca_completa(*colonne, q: str | None, max_len: int = 120):
    """
    AND sui token: ogni token deve comparire in almeno una colonna.
    Ordine delle parole irrilevante (Salvatore D'Amico ≡ D'Amico Salvatore).
    """
    tokens = token_ricerca(q, max_len=max_len)
    if not tokens or not colonne:
        return None
    and_parts = []
    for token in tokens:
        or_parts = []
        for col in colonne:
            for v in varianti_token(token):
                or_parts.append(col.ilike(f"%{v}%", escape="\\"))
        if or_parts:
            and_parts.append(or_(*or_parts))
    if not and_parts:
        return None
    return and_(*and_parts)


def applica_ricerca(query, *colonne, q: str | None, max_len: int = 120):
    """Applica filtro ricerca completa a una query SQLAlchemy."""
    cond = condizione_ricerca_completa(*colonne, q=q, max_len=max_len)
    if cond is None:
        return query
    return query.filter(cond)


def testo_coincide_ricerca(haystack: str | None, q: str | None) -> bool:
    """Match in-memory con le stesse regole (token + apostrofi)."""
    tokens = token_ricerca(q)
    if not tokens:
        return True
    base = unifica_apostrofi(haystack or "").casefold()
    base_senza = base.replace("'", "")
    for token in tokens:
        ok = False
        for v in varianti_token(token):
            needle = v.replace("\\%", "%").replace("\\_", "_").replace("\\\\", "\\")
            if "%" in needle:
                # jolly: confronta senza apostrofo
                parti = [p for p in needle.split("%") if p]
                cursore = 0
                tmp = base
                match = True
                for p in parti:
                    idx = tmp.find(p, cursore)
                    if idx < 0:
                        match = False
                        break
                    cursore = idx + len(p)
                if match:
                    ok = True
                    break
            elif needle in base or needle.replace("'", "") in base_senza:
                ok = True
                break
        if not ok:
            return False
    return True
