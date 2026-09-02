"""Ranking "em alta": perfumes com mais atividade recente.

Atividade = reviews novas + atualizações de review + favoritos (novos ou
virados "tenho") nos últimos N dias.

Calculado em Python com três queries simples (uma por tipo de evento),
não com `annotate`+`Count` combinando `reviews`, `reviews__updates` e
`favorited_by` na mesma query — três relações reversas diferentes
combinadas assim multiplicam linhas entre os joins antes de contar,
igual ao problema já documentado em `recommendations.py` pra múltiplas
relações M2M. Catálogo pequeno no MVP; se crescer muito, isso pode virar
uma agregação no banco (ex.: uma tabela de eventos única) ou um cache.
"""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from catalog.models import Perfume
from favorites.models import Favorite
from reviews.models import Review, ReviewUpdate

DEFAULT_WINDOW_DAYS = 30


def trending_perfumes(days: int = DEFAULT_WINDOW_DAYS, limit: int = 10) -> list[Perfume]:
    """Perfumes com mais reviews/atualizações/favoritos nos últimos `days` dias."""
    cutoff = timezone.now() - timedelta(days=days)

    counts: dict[int, int] = {}

    def _count(perfume_ids) -> None:
        for perfume_id in perfume_ids:
            counts[perfume_id] = counts.get(perfume_id, 0) + 1

    _count(Review.objects.filter(created_at__gte=cutoff).values_list("perfume_id", flat=True))
    _count(ReviewUpdate.objects.filter(created_at__gte=cutoff).values_list("review__perfume_id", flat=True))
    _count(Favorite.objects.filter(created_at__gte=cutoff).values_list("perfume_id", flat=True))

    if not counts:
        return []

    ranked_ids = sorted(counts, key=lambda perfume_id: counts[perfume_id], reverse=True)[:limit]
    perfumes_by_id = {p.id: p for p in Perfume.objects.filter(pk__in=ranked_ids).select_related("brand")}

    result = []
    for perfume_id in ranked_ids:
        perfume = perfumes_by_id.get(perfume_id)
        if perfume is not None:
            perfume.activity_count = counts[perfume_id]
            result.append(perfume)
    return result
