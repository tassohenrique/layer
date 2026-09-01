"""Regras de sazonalidade (hemisfério sul, calendário do Brasil)."""
from __future__ import annotations

import datetime as _dt
from enum import Enum


class Season(str, Enum):
    VERAO = "verao"
    INVERNO = "inverno"
    PRIMAVERA = "primavera"
    OUTONO = "outono"


SEASON_LABELS_PT: dict[Season, str] = {
    Season.VERAO: "Verão",
    Season.INVERNO: "Inverno",
    Season.PRIMAVERA: "Primavera",
    Season.OUTONO: "Outono",
}

# Meses -> estação, seguindo o calendário meteorológico do hemisfério sul
# (Brasil), onde dezembro/janeiro/fevereiro são verão, e assim por diante.
_MONTH_TO_SEASON: dict[int, Season] = {
    12: Season.VERAO, 1: Season.VERAO, 2: Season.VERAO,
    3: Season.OUTONO, 4: Season.OUTONO, 5: Season.OUTONO,
    6: Season.INVERNO, 7: Season.INVERNO, 8: Season.INVERNO,
    9: Season.PRIMAVERA, 10: Season.PRIMAVERA, 11: Season.PRIMAVERA,
}


def season_from_date(date: _dt.date) -> Season:
    """Deduz a estação (hemisfério sul) a partir de uma data do calendário."""
    return _MONTH_TO_SEASON[date.month]


def current_season() -> Season:
    """Estação atual, útil para sugestões automáticas ("hoje está frio")."""
    return season_from_date(_dt.date.today())


def is_in_season(fragrance_best_seasons: list[Season] | list[str], season: Season) -> bool:
    """Verifica se uma fragrância está entre as recomendadas para a estação dada.

    Uma fragrância sem estação declarada é tratada como "coringa" (serve em
    qualquer estação) em vez de ser excluída por falta de dado.
    """
    if not fragrance_best_seasons:
        return True
    normalized = {Season(s) if not isinstance(s, Season) else s for s in fragrance_best_seasons}
    return season in normalized
