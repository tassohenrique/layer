"""Recomendador simples: "quem gosta desse perfume também pode gostar de...".

Sem ML — pontua por sobreposição de accords e notas com o perfume de
referência. `legacy/layer/domain/compatibility.py` resolve um problema
diferente (layering: como DUAS fragrâncias combinam quando usadas juntas,
com regras de papel líder/modificador) e não se aplica aqui: isso é
similaridade entre catálogo, pra sugerir o PRÓXIMO perfume a experimentar,
não uma combinação.

Calculado em Python sobre querysets pré-carregados, não com `annotate` +
`Count` em várias relações M2M na mesma query — o Django infla a
contagem quando combina mais de uma anotação M2M assim. Catálogo é
pequeno no MVP (dezenas de perfumes); se crescer muito, isso pode
precisar virar uma query mais esperta ou um cache.
"""
from __future__ import annotations

from catalog.models import Perfume

ACCORD_WEIGHT = 3
NOTE_WEIGHT = 1


def _note_ids(perfume: Perfume) -> set[int]:
    return (
        {n.id for n in perfume.notes_top.all()}
        | {n.id for n in perfume.notes_heart.all()}
        | {n.id for n in perfume.notes_base.all()}
    )


def similar_perfumes(perfume: Perfume, limit: int = 5) -> list[Perfume]:
    """Perfumes do catálogo mais parecidos com `perfume`, por accords/notas em comum."""
    accord_ids = {a.id for a in perfume.accords.all()}
    note_ids = _note_ids(perfume)

    if not accord_ids and not note_ids:
        return []

    candidates = (
        Perfume.objects.exclude(pk=perfume.pk)
        .select_related("brand")
        .prefetch_related("accords", "notes_top", "notes_heart", "notes_base")
    )

    scored: list[tuple[int, Perfume]] = []
    for candidate in candidates:
        shared_accords = len(accord_ids & {a.id for a in candidate.accords.all()})
        shared_notes = len(note_ids & _note_ids(candidate))
        score = shared_accords * ACCORD_WEIGHT + shared_notes * NOTE_WEIGHT
        if score > 0:
            scored.append((score, candidate))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [candidate for _, candidate in scored[:limit]]
