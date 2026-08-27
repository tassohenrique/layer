"""Motor de compatibilidade de layering — o coração do app.

Dado um par de fragrâncias, o motor:

1. Busca a regra de compatibilidade entre as famílias olfativas (matriz em
   ``families.py``) — o componente de maior peso no score final.
2. Ajusta o score por diferença de intensidade (choque de protagonismo
   quando duas fragrâncias fortes disputam espaço).
3. Ajusta por sobreposição de estação recomendada.
4. Ajusta por concentração (dois Extraits fortes pedem cautela).
5. Decide qual fragrância lidera a combinação (papel líder/modificador) e
   gera instruções de aplicação e uma explicação em português.

O motor nunca bloqueia uma combinação — mesmo pares "arriscados" são
retornados, apenas sinalizados como experimentais.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from layer.domain.families import SWEET_CLUSTER, OlfactoryFamily, get_family_pair_rule
from layer.domain.seasons import Season
from layer.schemas import FragranceRead

# --- Constantes de negócio -------------------------------------------------

# Concentração -> "força" relativa, usada no desempate de papel líder/modificador.
_CONCENTRATION_RANK: dict[str, int] = {"cologne": 1, "edt": 2, "edp": 3, "extrait": 4}

# Intenções que preferem uma categoria específica da matriz de famílias.
_INTENTION_TO_CATEGORY: dict[str, str] = {
    "ecoar": "reforco",
    "suavizar": "suaviza",
    "contrastar": "contraste",
}

# Famílias que "clareiam" e "escurecem" uma composição — usadas pelas
# intenções `clarear` e `escurecer`, que não mapeiam para uma categoria fixa
# da matriz, mas para uma direção olfativa.
_LIGHTEN_FAMILIES: frozenset[OlfactoryFamily] = frozenset({
    OlfactoryFamily.CITRICO, OlfactoryFamily.VERDE, OlfactoryFamily.CHA, OlfactoryFamily.AROMATICO,
})
_DARKEN_FAMILIES: frozenset[OlfactoryFamily] = frozenset({
    OlfactoryFamily.AMBAR, OlfactoryFamily.OUD, OlfactoryFamily.COURO,
    OlfactoryFamily.RESINA, OlfactoryFamily.GOURMAND,
})


@dataclass(slots=True)
class ComboSuggestion:
    """Resultado da avaliação de um par de fragrâncias pelo motor."""

    base_fragrance: FragranceRead  # papel "líder" (aplicado na pele)
    modifier_fragrance: FragranceRead  # papel "modificador" (pulso/roupa)
    compatibility_score: int
    category: str
    is_experimental: bool
    rationale: str
    application_notes: str
    best_season: list[Season] = field(default_factory=list)


def assign_roles(fragrance_a: FragranceRead, fragrance_b: FragranceRead) -> tuple[FragranceRead, FragranceRead]:
    """Decide qual fragrância é a "base/líder" e qual é a "modificadora".

    Regra de perfumaria: lidera quem tem presença mais forte no conjunto —
    isso é aproximado, em ordem de prioridade, por maior intensidade
    declarada, depois maior concentração (extrait > edp > edt > cologne) e,
    por fim, maior número de notas de fundo (mais presença no dry-down).
    Em empate total, o desempate é pelo id (determinístico e estável).
    """

    def sort_key(f: FragranceRead) -> tuple[int, int, int]:
        return (f.intensity, _CONCENTRATION_RANK[f.concentration.value], len(f.notes_base))

    key_a, key_b = sort_key(fragrance_a), sort_key(fragrance_b)
    if key_a == key_b:
        # Desempate determinístico: menor id vira o líder.
        if fragrance_a.id is not None and fragrance_b.id is not None and fragrance_b.id < fragrance_a.id:
            return fragrance_b, fragrance_a
        return fragrance_a, fragrance_b
    if key_a > key_b:
        return fragrance_a, fragrance_b
    return fragrance_b, fragrance_a


def _intensity_adjustment(leader: FragranceRead, modifier: FragranceRead, same_family: bool) -> tuple[int, bool]:
    """Ajuste por diferença de intensidade.

    Duas fragrâncias fortes (intensidade >= 4), muito próximas em
    intensidade e da MESMA família disputam protagonismo em vez de se
    somarem — o cenário clássico de "choque de protagonismo" citado nas
    regras de perfumaria. Entre famílias diferentes, duas fragrâncias fortes
    não competem do mesmo jeito (é comum em nicho combinar dois pesos
    pesados de perfis distintos), então não há penalidade aí. Uma leve
    assimetria de intensidade (diff 1-2) é o ideal de layering (uma
    fragrância clara e outra de apoio), por isso ganha um pequeno bônus.
    """
    diff = abs(leader.intensity - modifier.intensity)
    both_high = leader.intensity >= 4 and modifier.intensity >= 4
    if same_family and both_high and diff <= 1:
        return -45, True
    if diff in (1, 2):
        return 6, False
    return 0, False


def _season_adjustment(leader: FragranceRead, modifier: FragranceRead) -> int:
    """Bônus se as estações recomendadas das duas fragrâncias se sobrepõem."""
    if not leader.best_season or not modifier.best_season:
        return 0
    overlap = set(leader.best_season) & set(modifier.best_season)
    return 10 if overlap else -5


def _concentration_adjustment(leader: FragranceRead, modifier: FragranceRead) -> int:
    """Penaliza levemente dois Extraits fortes combinados sem cuidado."""
    if leader.concentration.value == "extrait" and modifier.concentration.value == "extrait":
        return -10
    return 0


def _sweet_clash_adjustment(leader: FragranceRead, modifier: FragranceRead) -> tuple[int, bool]:
    """Detecta dois dominantes gourmand/oriental muito doces e fortes juntos."""
    if (
        leader.primary_family in SWEET_CLUSTER
        and modifier.primary_family in SWEET_CLUSTER
        and leader.intensity >= 4
        and modifier.intensity >= 4
    ):
        return -20, True
    return 0, False


def _build_application_notes(leader: FragranceRead, modifier: FragranceRead) -> str:
    return (
        f"1) {leader.name}: 2-3 borrifadas na pele (pontos de pulso, pescoço) — aplique primeiro, "
        f"ele lidera a combinação.\n"
        f"2) {modifier.name}: 1-2 borrifadas por cima ou na roupa — ele modula sem competir com o líder."
    )


def _build_rationale(leader: FragranceRead, modifier: FragranceRead, rule_rationale: str, highlight: bool) -> str:
    text = rule_rationale.format(lider=leader.name, modificador=modifier.name)
    if highlight:
        text = f"★ Contraste elegante: {text}"
    return text


def evaluate_pair(fragrance_a: FragranceRead, fragrance_b: FragranceRead) -> ComboSuggestion:
    """Avalia um par de fragrâncias e retorna uma sugestão de layering completa."""
    leader, modifier = assign_roles(fragrance_a, fragrance_b)
    same_family = leader.primary_family == modifier.primary_family
    rule = get_family_pair_rule(leader.primary_family, modifier.primary_family)

    score = rule.base_score
    is_experimental = rule.category == "arriscado"

    intensity_delta, intensity_risk = _intensity_adjustment(leader, modifier, same_family)
    score += intensity_delta
    is_experimental = is_experimental or intensity_risk

    score += _season_adjustment(leader, modifier)
    score += _concentration_adjustment(leader, modifier)

    sweet_delta, sweet_risk = _sweet_clash_adjustment(leader, modifier)
    score += sweet_delta
    is_experimental = is_experimental or sweet_risk

    score = max(0, min(100, score))

    overlap_season = sorted(
        set(leader.best_season) & set(modifier.best_season),
        key=lambda s: s.value,
    ) or leader.best_season or modifier.best_season

    return ComboSuggestion(
        base_fragrance=leader,
        modifier_fragrance=modifier,
        compatibility_score=score,
        category=rule.category,
        is_experimental=is_experimental,
        rationale=_build_rationale(leader, modifier, rule.rationale_pt, rule.highlight),
        application_notes=_build_application_notes(leader, modifier),
        best_season=list(overlap_season),
    )


def _apply_intention_bias(suggestion: ComboSuggestion, intention: str) -> int:
    """Reponta o score de acordo com a intenção declarada pelo usuário.

    `ecoar`/`suavizar`/`contrastar` mapeiam direto para uma categoria da
    matriz de famílias. `clarear`/`escurecer` não são uma categoria da
    matriz, e sim uma direção olfativa — por isso são avaliadas olhando a
    família do modificador (quem "empresta" a característica ao líder).
    """
    score = suggestion.compatibility_score
    preferred_category = _INTENTION_TO_CATEGORY.get(intention)
    if preferred_category and suggestion.category == preferred_category:
        score += 8
    elif intention == "clarear" and suggestion.modifier_fragrance.primary_family in _LIGHTEN_FAMILIES:
        score += 8
    elif intention == "escurecer" and suggestion.modifier_fragrance.primary_family in _DARKEN_FAMILIES:
        score += 8
    return max(0, min(100, score))


def _apply_occasion_season_bias(suggestion: ComboSuggestion, occasion: str | None, season: str | None) -> int:
    """Bônus leve quando a combinação combina com a ocasião/estação pedida."""
    score = suggestion.compatibility_score
    leader, modifier = suggestion.base_fragrance, suggestion.modifier_fragrance

    if season is not None:
        season_enum = Season(season)
        if season_enum in leader.best_season or season_enum in modifier.best_season:
            score += 6

    if occasion is not None:
        avg_intensity = (leader.intensity + modifier.intensity) / 2
        if occasion in ("noite", "especial") and avg_intensity >= 3:
            score += 5
        elif occasion in ("dia", "trabalho") and avg_intensity <= 3:
            score += 5

    return max(0, min(100, score))


def suggest_combos(
    fragrance_id: int,
    collection: list[FragranceRead],
    top_n: int = 5,
) -> list[ComboSuggestion]:
    """Sugere os melhores parceiros de layering, da coleção, para uma fragrância dada."""
    target = next((f for f in collection if f.id == fragrance_id), None)
    if target is None:
        raise ValueError(f"Fragrância {fragrance_id} não encontrada na coleção fornecida.")

    candidates = [f for f in collection if f.id != fragrance_id and f.owned]
    suggestions = [evaluate_pair(target, other) for other in candidates]
    suggestions.sort(key=lambda s: s.compatibility_score, reverse=True)
    return suggestions[:top_n]


def suggest_from_scratch(
    collection: list[FragranceRead],
    intention: str,
    occasion: str | None = None,
    season: str | None = None,
    top_n: int = 10,
) -> list[ComboSuggestion]:
    """Varre a coleção inteira e sugere os melhores pares dado um objetivo.

    Diferente de bloquear por ocasião/estação, o motor aplica um bônus suave
    quando a combinação se encaixa no pedido — mantendo o espírito de
    "avisar, não proibir" mesmo nas sugestões "do zero".
    """
    owned = [f for f in collection if f.owned]
    suggestions: list[ComboSuggestion] = []
    for frag_a, frag_b in itertools.combinations(owned, 2):
        suggestion = evaluate_pair(frag_a, frag_b)
        suggestion.compatibility_score = _apply_intention_bias(suggestion, intention)
        suggestion.compatibility_score = _apply_occasion_season_bias(suggestion, occasion, season)
        suggestions.append(suggestion)

    suggestions.sort(key=lambda s: s.compatibility_score, reverse=True)
    return suggestions[:top_n]
