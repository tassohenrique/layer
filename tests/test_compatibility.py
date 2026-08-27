"""Testes do motor de compatibilidade — a lógica de negócio mais importante do app."""
from __future__ import annotations

from layer.domain.compatibility import assign_roles, evaluate_pair, suggest_combos, suggest_from_scratch
from layer.schemas import FragranceRead


def make_fragrance(
    id: int,
    name: str,
    *,
    primary_family: str,
    secondary_family: str | None = None,
    intensity: int = 3,
    concentration: str = "edp",
    best_season: list[str] | None = None,
    notes_base: list[str] | None = None,
    owned: bool = True,
) -> FragranceRead:
    """Fábrica de FragranceRead para os testes, sem precisar de banco."""
    return FragranceRead(
        id=id,
        name=name,
        brand="Marca Teste",
        house_type="nicho",
        gender="unissex",
        concentration=concentration,
        intensity=intensity,
        longevity_hours=8,
        primary_family=primary_family,
        secondary_family=secondary_family,
        notes_top=[],
        notes_heart=[],
        notes_base=notes_base or ["nota-base"],
        best_season=best_season or [],
        owned=owned,
        bottle_ml=100,
        ml_remaining=100,
        personal_rating=None,
        price_tier=2,
        notes_pessoais="",
    )


class TestParDeReforco:
    def test_amadeirado_e_ambar_reforcam(self) -> None:
        vetiver = make_fragrance(1, "Vetiver Base", primary_family="amadeirado", intensity=3)
        oriental = make_fragrance(2, "Oriental Suave", primary_family="ambar", intensity=2)

        result = evaluate_pair(vetiver, oriental)

        assert result.category == "reforco"
        assert result.compatibility_score >= 80
        assert not result.is_experimental

    def test_rationale_menciona_os_dois_nomes(self) -> None:
        a = make_fragrance(1, "Fragrância A", primary_family="citrico", intensity=3)
        b = make_fragrance(2, "Fragrância B", primary_family="aromatico", intensity=2)

        result = evaluate_pair(a, b)

        assert "Fragrância A" in result.rationale
        assert "Fragrância B" in result.rationale


class TestParDeContraste:
    def test_gourmand_e_couro_e_contraste_com_destaque(self) -> None:
        gourmand = make_fragrance(1, "Doce Denso", primary_family="gourmand", intensity=4)
        couro = make_fragrance(2, "Couro Seco", primary_family="couro", intensity=2)

        result = evaluate_pair(gourmand, couro)

        assert result.category == "contraste"
        assert 70 <= result.compatibility_score <= 100
        assert result.rationale.startswith("★")

    def test_vetiver_seco_quebra_doce_do_ambar(self) -> None:
        vetiver_seco = make_fragrance(1, "Vetiver Puro", primary_family="amadeirado_seco", intensity=3)
        ambar_doce = make_fragrance(2, "Âmbar Baunilhado", primary_family="ambar", intensity=2)

        result = evaluate_pair(vetiver_seco, ambar_doce)

        assert result.category == "contraste"
        assert result.compatibility_score >= 75


class TestParArriscado:
    def test_aquatico_e_gourmand_pesado_e_sinalizado_mas_nao_bloqueado(self) -> None:
        aquatico = make_fragrance(1, "Brisa do Mar", primary_family="aquatico", intensity=3)
        gourmand_pesado = make_fragrance(2, "Bomba Doce", primary_family="gourmand", intensity=3)

        result = evaluate_pair(aquatico, gourmand_pesado)

        assert result.category == "arriscado"
        assert result.is_experimental is True
        assert result.compatibility_score <= 45
        # O motor nunca bloqueia — sempre retorna uma sugestão utilizável.
        assert result.base_fragrance is not None
        assert result.modifier_fragrance is not None
        assert result.application_notes != ""

    def test_dois_fortes_mesma_familia_geram_choque_de_protagonismo(self) -> None:
        forte_1 = make_fragrance(1, "Amadeirado Forte 1", primary_family="amadeirado", intensity=5)
        forte_2 = make_fragrance(2, "Amadeirado Forte 2", primary_family="amadeirado", intensity=4)

        result = evaluate_pair(forte_1, forte_2)

        assert result.is_experimental is True
        # Base de reforço (mesma família) parte de ~78, mas o choque de
        # protagonismo (-45) deve derrubar bastante o score final.
        assert result.compatibility_score <= 45


class TestAtribuicaoDePapelLiderModificador:
    def test_maior_intensidade_vira_lider(self) -> None:
        forte = make_fragrance(1, "Forte", primary_family="amadeirado", intensity=5)
        fraco = make_fragrance(2, "Fraco", primary_family="floral", intensity=2)

        leader, modifier = assign_roles(forte, fraco)

        assert leader.id == 1
        assert modifier.id == 2

    def test_empate_de_intensidade_desempata_por_concentracao(self) -> None:
        extrait = make_fragrance(1, "Extrait", primary_family="amadeirado", intensity=3, concentration="extrait")
        edt = make_fragrance(2, "EDT", primary_family="floral", intensity=3, concentration="edt")

        leader, modifier = assign_roles(extrait, edt)

        assert leader.id == 1
        assert modifier.id == 2

    def test_empate_total_desempata_por_id(self) -> None:
        a = make_fragrance(5, "A", primary_family="amadeirado", intensity=3, concentration="edp", notes_base=["x"])
        b = make_fragrance(2, "B", primary_family="floral", intensity=3, concentration="edp", notes_base=["y"])

        leader, modifier = assign_roles(a, b)

        assert leader.id == 2  # menor id vence o empate total
        assert modifier.id == 5

    def test_aplicacao_recomenda_lider_na_pele_e_modificador_por_cima(self) -> None:
        forte = make_fragrance(1, "Líder Esperado", primary_family="amadeirado", intensity=5)
        fraco = make_fragrance(2, "Modificador Esperado", primary_family="floral", intensity=2)

        result = evaluate_pair(forte, fraco)

        assert result.base_fragrance.id == 1
        assert result.modifier_fragrance.id == 2
        assert "Líder Esperado" in result.application_notes
        assert "Modificador Esperado" in result.application_notes


class TestSuggestCombos:
    def test_ordena_por_score_decrescente(self) -> None:
        alvo = make_fragrance(1, "Alvo", primary_family="amadeirado", intensity=3)
        bom_par = make_fragrance(2, "Bom Par", primary_family="ambar", intensity=2)
        par_arriscado = make_fragrance(3, "Par Arriscado", primary_family="amadeirado", intensity=5)
        colecao = [alvo, bom_par, par_arriscado]

        suggestions = suggest_combos(1, colecao)

        assert len(suggestions) == 2
        assert suggestions[0].compatibility_score >= suggestions[1].compatibility_score

    def test_ignora_fragrancias_nao_possuidas(self) -> None:
        alvo = make_fragrance(1, "Alvo", primary_family="amadeirado", intensity=3)
        nao_possuido = make_fragrance(2, "Não Tenho", primary_family="ambar", intensity=2, owned=False)

        suggestions = suggest_combos(1, [alvo, nao_possuido])

        assert suggestions == []


class TestSuggestFromScratch:
    def test_intencao_ecoar_favorece_pares_de_reforco(self) -> None:
        a = make_fragrance(1, "A", primary_family="amadeirado", intensity=3, best_season=["inverno"])
        b = make_fragrance(2, "B", primary_family="ambar", intensity=2, best_season=["inverno"])
        c = make_fragrance(3, "C", primary_family="aquatico", intensity=3, best_season=["verao"])
        d = make_fragrance(4, "D", primary_family="gourmand", intensity=3, best_season=["verao"])

        suggestions = suggest_from_scratch([a, b, c, d], intention="ecoar")

        assert suggestions[0].category == "reforco"
