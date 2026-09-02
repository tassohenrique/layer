import pytest

from catalog.models import Accord, Brand, Note, Perfume
from catalog.recommendations import similar_perfumes

pytestmark = pytest.mark.django_db


def make_perfume(name: str, **overrides) -> Perfume:
    brand = overrides.pop("brand", None) or Brand.objects.create(name=f"Marca {name}")
    return Perfume.objects.create(brand=brand, name=name, concentration="edp", **overrides)


class TestSimilarPerfumes:
    def test_sem_accords_nem_notas_retorna_vazio(self) -> None:
        alvo = make_perfume("Sem dados")
        make_perfume("Outro")

        assert similar_perfumes(alvo) == []

    def test_prioriza_quem_compartilha_mais_accords(self) -> None:
        oud = Accord.objects.create(key="oud", label_pt="Oud")
        floral = Accord.objects.create(key="floral", label_pt="Floral")
        gourmand = Accord.objects.create(key="gourmand", label_pt="Gourmand")

        alvo = make_perfume("Alvo")
        alvo.accords.add(oud, floral)

        muito_parecido = make_perfume("Muito parecido")
        muito_parecido.accords.add(oud, floral)

        pouco_parecido = make_perfume("Pouco parecido")
        pouco_parecido.accords.add(oud)

        sem_nada_em_comum = make_perfume("Sem nada em comum")
        sem_nada_em_comum.accords.add(gourmand)

        result = similar_perfumes(alvo)

        assert result[0] == muito_parecido
        assert result[1] == pouco_parecido
        assert sem_nada_em_comum not in result

    def test_nota_em_comum_tambem_conta(self) -> None:
        bergamota = Note.objects.create(name="Bergamota")
        alvo = make_perfume("Alvo")
        alvo.notes_top.add(bergamota)

        parecido = make_perfume("Parecido")
        parecido.notes_top.add(bergamota)

        result = similar_perfumes(alvo)

        assert parecido in result

    def test_nao_inclui_o_proprio_perfume(self) -> None:
        oud = Accord.objects.create(key="oud", label_pt="Oud")
        alvo = make_perfume("Alvo")
        alvo.accords.add(oud)

        result = similar_perfumes(alvo)

        assert alvo not in result

    def test_respeita_o_limite(self) -> None:
        oud = Accord.objects.create(key="oud", label_pt="Oud")
        alvo = make_perfume("Alvo")
        alvo.accords.add(oud)

        for i in range(10):
            p = make_perfume(f"Similar {i}")
            p.accords.add(oud)

        result = similar_perfumes(alvo, limit=3)

        assert len(result) == 3
