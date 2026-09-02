import datetime as dt

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from catalog.models import Brand, Perfume
from catalog.trending import trending_perfumes
from favorites.models import Favorite
from reviews.models import Review, ReviewUpdate

pytestmark = pytest.mark.django_db


def make_perfume(name: str) -> Perfume:
    brand = Brand.objects.create(name=f"Marca {name}")
    return Perfume.objects.create(brand=brand, name=name, concentration="edp")


class TestTrendingPerfumes:
    def test_sem_atividade_retorna_vazio(self) -> None:
        make_perfume("Parado")

        assert trending_perfumes() == []

    def test_review_recente_conta_como_atividade(self) -> None:
        perfume = make_perfume("Ativo")
        user = User.objects.create_user("u1", password="senha123")
        Review.objects.create(perfume=perfume, user=user, rating=5, text="")

        result = trending_perfumes()

        assert perfume in result
        assert result[0].activity_count == 1

    def test_favorito_recente_conta_como_atividade(self) -> None:
        perfume = make_perfume("Favoritado")
        user = User.objects.create_user("u1", password="senha123")
        Favorite.objects.create(user=user, perfume=perfume)

        result = trending_perfumes()

        assert perfume in result

    def test_atualizacao_de_review_conta_como_atividade(self) -> None:
        perfume = make_perfume("Atualizado")
        user = User.objects.create_user("u1", password="senha123")
        review = Review.objects.create(perfume=perfume, user=user, rating=3, text="")
        ReviewUpdate.objects.create(review=review, rating=5, text="Melhorou")

        result = trending_perfumes()

        # 1 review + 1 atualização = 2 atividades
        assert result[0].pk == perfume.pk
        assert result[0].activity_count == 2

    def test_atividade_fora_da_janela_nao_conta(self) -> None:
        perfume = make_perfume("Velho")
        user = User.objects.create_user("u1", password="senha123")
        review = Review.objects.create(perfume=perfume, user=user, rating=5, text="")
        old_date = timezone.now() - dt.timedelta(days=60)
        Review.objects.filter(pk=review.pk).update(created_at=old_date)

        result = trending_perfumes(days=30)

        assert perfume not in result

    def test_ordena_por_mais_atividade_primeiro(self) -> None:
        muito_ativo = make_perfume("Muito ativo")
        pouco_ativo = make_perfume("Pouco ativo")
        u1 = User.objects.create_user("u1", password="senha123")
        u2 = User.objects.create_user("u2", password="senha123")
        Review.objects.create(perfume=muito_ativo, user=u1, rating=5, text="")
        Favorite.objects.create(user=u1, perfume=muito_ativo)
        Favorite.objects.create(user=u2, perfume=pouco_ativo)

        result = trending_perfumes()

        assert result[0] == muito_ativo
        assert result[1] == pouco_ativo

    def test_respeita_o_limite(self) -> None:
        for i in range(5):
            perfume = make_perfume(f"Perfume {i}")
            user = User.objects.create_user(f"u{i}", password="senha123")
            Review.objects.create(perfume=perfume, user=user, rating=5, text="")

        result = trending_perfumes(limit=2)

        assert len(result) == 2


class TestTrendingView:
    def test_pagina_lista_perfumes_em_alta(self, client) -> None:
        perfume = make_perfume("Em Alta")
        user = User.objects.create_user("u1", password="senha123")
        Review.objects.create(perfume=perfume, user=user, rating=5, text="")

        response = client.get(reverse("catalog:trending"))

        assert response.status_code == 200
        assert b"Em Alta" in response.content

    def test_pagina_acessivel_sem_login(self, client) -> None:
        response = client.get(reverse("catalog:trending"))
        assert response.status_code == 200
