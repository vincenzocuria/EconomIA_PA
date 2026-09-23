"""Ordine del registro movimenti: data, poi ora, poi id."""

from app.models.movimento import Movimento


def ordina_movimenti(query):
    return query.order_by(
        Movimento.data_movimento.desc(),
        Movimento.ora_movimento.desc(),
        Movimento.id.desc(),
    )
