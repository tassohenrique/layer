import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse

from catalog.models import Accord, Brand, Note, Perfume
from reviews.models import Review

pytestmark = pytest.mark.django_db


def make_perfume(**overrides) -> Perfume:
    brand = overrides.pop("brand", None) or Brand.objects.create(name="Marca Teste")
    defaults = dict(brand=brand, name="Perfume Teste", concentration="edp")
    defaults.update(overrides)
    return Perfume.objects.create(**defaults)


class TestPerfumeModel:
    def test_slug_gerado_automaticamente(self) -> None:
        perfume = make_perfume(name="Naxos")
        assert perfume.slug == "marca-teste-naxos"

    def test_slug_nao_colide_quando_marca_e_nome_diferentes_geram_o_mesmo_texto(self) -> None:
        # "A B" + "C" e "A" + "B C" produzem o mesmo slug bruto ("a-b-c") sem
        # violar o unique_together (brand, name), já que marca e nome diferem.
        p1 = make_perfume(brand=Brand.objects.create(name="A B"), name="C")
        p2 = make_perfume(brand=Brand.objects.create(name="A"), name="B C")
        assert p1.slug != p2.slug

    def test_rating_stats_sem_reviews(self) -> None:
        perfume = make_perfume()
        stats = perfume.rating_stats
        assert stats == {"average": 0, "count": 0}

    def test_rating_stats_com_reviews(self) -> None:
        perfume = make_perfume()
        u1 = User.objects.create_user("u1", password="x")
        u2 = User.objects.create_user("u2", password="x")
        Review.objects.create(perfume=perfume, user=u1, rating=5, text="")
        Review.objects.create(perfume=perfume, user=u2, rating=3, text="")

        stats = perfume.rating_stats

        assert stats["count"] == 2
        assert stats["average"] == 4


class TestPerfumeViews:
    def test_lista_mostra_perfumes(self, client) -> None:
        make_perfume(name="Interlude Man")

        response = client.get(reverse("catalog:perfume_list"))

        assert response.status_code == 200
        assert b"Interlude Man" in response.content

    def test_detalhe_mostra_piramide_e_accords(self, client) -> None:
        perfume = make_perfume(name="Santal 33")
        note = Note.objects.create(name="Bergamota")
        perfume.notes_top.add(note)
        accord = Accord.objects.create(key="amadeirado", label_pt="Amadeirado")
        perfume.accords.add(accord)

        response = client.get(perfume.get_absolute_url())

        assert response.status_code == 200
        assert b"Bergamota" in response.content
        assert "Amadeirado".encode() in response.content


class TestSeedCommand:
    def test_seed_e_idempotente(self) -> None:
        call_command("seed_perfumes")
        total_after_first = Perfume.objects.count()

        call_command("seed_perfumes")

        assert Perfume.objects.count() == total_after_first
        assert total_after_first == 20
