"""Famílias olfativas e a matriz de compatibilidade entre elas.

A matriz codifica, como dados (não como texto solto), o conhecimento de
perfumaria usado pelo motor de sugestão em ``domain/compatibility.py``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OlfactoryFamily(str, Enum):
    """Famílias olfativas reconhecidas pelo app.

    Algumas famílias "clássicas" foram desdobradas em variantes porque a
    regra de perfumaria muda de comportamento conforme a variante:
    ``AMADEIRADO`` vs ``AMADEIRADO_SECO`` (ex.: vetiver, que contrasta bem
    com doces) e ``ALMISCARADO`` (almíscar limpo) vs
    ``ALMISCARADO_ANIMALICO`` (almíscar animálico, mais arriscado).
    """

    CITRICO = "citrico"
    AROMATICO = "aromatico"
    VERDE = "verde"
    FLORAL = "floral"
    ESPECIADO = "especiado"
    AMADEIRADO = "amadeirado"
    AMADEIRADO_SECO = "amadeirado_seco"
    RESINA = "resina"
    INCENSO = "incenso"
    AMBAR = "ambar"
    OUD = "oud"
    GOURMAND = "gourmand"
    COURO = "couro"
    ALMISCARADO = "almiscarado"
    ALMISCARADO_ANIMALICO = "almiscarado_animalico"
    AQUATICO = "aquatico"
    CHA = "cha"


FAMILY_LABELS_PT: dict[OlfactoryFamily, str] = {
    OlfactoryFamily.CITRICO: "Cítrico",
    OlfactoryFamily.AROMATICO: "Aromático/Fougère",
    OlfactoryFamily.VERDE: "Verde",
    OlfactoryFamily.FLORAL: "Floral",
    OlfactoryFamily.ESPECIADO: "Especiado",
    OlfactoryFamily.AMADEIRADO: "Amadeirado",
    OlfactoryFamily.AMADEIRADO_SECO: "Amadeirado Seco",
    OlfactoryFamily.RESINA: "Resinoso",
    OlfactoryFamily.INCENSO: "Incenso",
    OlfactoryFamily.AMBAR: "Âmbar/Oriental",
    OlfactoryFamily.OUD: "Oud",
    OlfactoryFamily.GOURMAND: "Gourmand",
    OlfactoryFamily.COURO: "Couro/Tabaco/Fumaça",
    OlfactoryFamily.ALMISCARADO: "Almiscarado (limpo)",
    OlfactoryFamily.ALMISCARADO_ANIMALICO: "Almiscarado Animálico",
    OlfactoryFamily.AQUATICO: "Aquático/Ozônico",
    OlfactoryFamily.CHA: "Chá",
}


@dataclass(frozen=True, slots=True)
class PairRule:
    """Regra de compatibilidade entre duas famílias olfativas.

    ``base_score`` é o ponto de partida (0-100) usado pelo motor antes dos
    ajustes de intensidade, estação e concentração.
    """

    base_score: int
    category: str  # "reforco" | "suaviza" | "contraste" | "arriscado" | "neutro"
    rationale_pt: str
    highlight: bool = False


_F = OlfactoryFamily

# Pares que reforçam/ecoam bem (score alto, ~80-95).
_REFORCO: dict[frozenset[_F], PairRule] = {
    frozenset({_F.AMADEIRADO, _F.AMBAR}): PairRule(
        88, "reforco",
        "{lider} e {modificador} ecoam: a base amadeirada sustenta o âmbar/oriental, "
        "criando uma trilha contínua sem quebras.",
    ),
    frozenset({_F.CITRICO, _F.AROMATICO}): PairRule(
        85, "reforco",
        "O cítrico de {lider} se funde à espinha aromática de {modificador}, "
        "reforçando a sensação fresca do conjunto.",
    ),
    frozenset({_F.CITRICO, _F.VERDE}): PairRule(
        84, "reforco",
        "Cítrico e verde compartilham a mesma família de frescor, então "
        "{lider} e {modificador} se somam em vez de competir.",
    ),
    frozenset({_F.INCENSO, _F.AMADEIRADO}): PairRule(
        86, "reforco",
        "O incenso de {lider} agarra na madeira de {modificador}, prolongando "
        "a sensação de fumaça seca sobre uma base sólida.",
    ),
    frozenset({_F.ESPECIADO, _F.AMBAR}): PairRule(
        87, "reforco",
        "Especiarias e âmbar são farinha do mesmo saco oriental: {lider} "
        "acentua o calor que {modificador} já traz de fundo.",
    ),
    frozenset({_F.INCENSO, _F.AMADEIRADO_SECO}): PairRule(
        84, "reforco",
        "A fumaça do incenso em {lider} gruda na secura da madeira de "
        "{modificador} do mesmo jeito que na madeira \"normal\" — o eco continua.",
    ),
    frozenset({_F.AMADEIRADO, _F.AMADEIRADO_SECO}): PairRule(
        80, "reforco",
        "{lider} e {modificador} são primas dentro da família amadeirada — "
        "a versão seca só afina o mesmo tema em vez de contrastar com ele.",
    ),
}

# Pares que suavizam (score ~70-85).
_SUAVIZA: dict[frozenset[_F], PairRule] = {
    frozenset({_F.FLORAL, _F.ALMISCARADO}): PairRule(
        78, "suaviza",
        "O almíscar limpo de {modificador} poliza as pétalas de {lider}, "
        "deixando o floral mais próximo da pele e menos declarado.",
    ),
    frozenset({_F.AMADEIRADO_SECO, _F.ALMISCARADO}): PairRule(
        76, "suaviza",
        "O almíscar arredonda as arestas secas da madeira de {lider}, "
        "resultando numa combinação mais macia e confortável.",
    ),
}

# Pares de contraste elegante (score ~75-90) — categoria mais valorizada em nicho.
_CONTRASTE: dict[frozenset[_F], PairRule] = {
    frozenset({_F.GOURMAND, _F.COURO}): PairRule(
        88, "contraste",
        "Contraste clássico de nicho: o couro/tabaco/fumaça de {modificador} "
        "corta o açúcar de {lider}, evitando que o gourmand fique enjoativo.",
        highlight=True,
    ),
    frozenset({_F.AMADEIRADO_SECO, _F.AMBAR}): PairRule(
        85, "contraste",
        "O vetiver seco de {lider} quebra a doçura do âmbar/baunilha de "
        "{modificador} sem apagar o fundo — combinação de contraste clássica.",
        highlight=True,
    ),
    frozenset({_F.AMADEIRADO_SECO, _F.GOURMAND}): PairRule(
        84, "contraste",
        "A secura amadeirada de {lider} disciplina o gourmand de "
        "{modificador}, dando estrutura a uma composição que sozinha seria só doce.",
        highlight=True,
    ),
    frozenset({_F.FLORAL, _F.OUD}): PairRule(
        83, "contraste",
        "A rosa/floral de {lider} suaviza a aspereza do oud/amadeirado de "
        "{modificador}, um contraste tradicional da perfumaria árabe revisitado em nicho.",
        highlight=True,
    ),
    frozenset({_F.ESPECIADO, _F.AMADEIRADO}): PairRule(
        82, "contraste",
        "O açafrão/especiarias de {lider} dão brilho picante à madeira mais "
        "quieta de {modificador}, um contraste elegante de textura.",
        highlight=True,
    ),
    frozenset({_F.ESPECIADO, _F.AMADEIRADO_SECO}): PairRule(
        80, "contraste",
        "As especiarias de {lider} dão brilho picante à secura amadeirada de "
        "{modificador}, o mesmo contraste de textura, só que mais árido.",
        highlight=True,
    ),
    frozenset({_F.RESINA, _F.CITRICO}): PairRule(
        79, "contraste",
        "O cítrico de {modificador} clareia a densidade resinosa de {lider}, "
        "abrindo espaço na composição sem perder o corpo.",
        highlight=True,
    ),
    frozenset({_F.FLORAL, _F.VERDE}): PairRule(
        81, "contraste",
        "O verde de {modificador} seca o doce floral de {lider}, um contraste "
        "clássico que evita o enjoo do floral puro.",
        highlight=True,
    ),
    frozenset({_F.FLORAL, _F.CHA}): PairRule(
        80, "contraste",
        "O chá de {modificador} seca e alonga o floral de {lider}, deixando "
        "a combinação mais etérea e menos doce.",
        highlight=True,
    ),
}

# Pares arriscados / score baixo (~20-40) — o app avisa, mas não bloqueia.
_ARRISCADO: dict[frozenset[_F], PairRule] = {
    frozenset({_F.AQUATICO, _F.GOURMAND}): PairRule(
        30, "arriscado",
        "Aquático/ozônico contra gourmand pesado tende a criar uma sensação "
        "estranha de \"doce molhado\" — experimental, use com cautela.",
    ),
    frozenset({_F.ALMISCARADO_ANIMALICO, _F.FLORAL}): PairRule(
        32, "arriscado",
        "Almíscar animálico forte pode brigar com um floral igualmente forte "
        "em vez de sustentá-lo — experimental, use com cautela.",
    ),
    frozenset({_F.GOURMAND, _F.AMBAR}): PairRule(
        38, "arriscado",
        "Dois dominantes doces (gourmand e âmbar/oriental) juntos correm o "
        "risco de ficar enjoativo se ambos forem intensos — experimental, use com cautela.",
    ),
}

PAIR_RULES: dict[frozenset[_F], PairRule] = {
    **_REFORCO,
    **_SUAVIZA,
    **_CONTRASTE,
    **_ARRISCADO,
}

_SAME_FAMILY_RULE = PairRule(
    78, "reforco",
    "{lider} e {modificador} são da mesma família olfativa, o que cria um "
    "efeito de eco natural quando as intensidades não competem entre si.",
)

_NEUTRAL_RULE = PairRule(
    55, "neutro",
    "{lider} e {modificador} não formam um par clássico de nicho, mas "
    "também não há contraindicação direta — o resultado pode variar bastante na pele.",
)

# Cluster de famílias "doces" usado pelo motor para detectar choque de
# protagonismo entre dois dominantes muito adocicados (ver compatibility.py).
SWEET_CLUSTER: frozenset[OlfactoryFamily] = frozenset({_F.GOURMAND, _F.AMBAR})


def get_family_pair_rule(family_a: OlfactoryFamily, family_b: OlfactoryFamily) -> PairRule:
    """Retorna a regra de compatibilidade para um par de famílias.

    Mesma família cai num caso especial de reforço (efeito eco); pares não
    catalogados caem no valor neutro padrão em vez de serem tratados como erro,
    pois o app nunca deve travar por falta de dado na matriz.
    """
    if family_a == family_b:
        return _SAME_FAMILY_RULE
    key = frozenset({family_a, family_b})
    return PAIR_RULES.get(key, _NEUTRAL_RULE)
