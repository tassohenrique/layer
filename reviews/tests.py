import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from catalog.models import Brand, Perfume
from reviews.models import Review, ReviewLike

pytestmark = pytest.mark.django_db


@pytest.fixture()
def perfume() -> Perfume:
    brand = Brand.objects.create(name="Marca Teste")
    return Perfume.objects.create(brand=brand, name="Perfume Teste", concentration="edp")


class TestCreateReview:
    def test_anonimo_e_redirecionado_pro_login(self, client, perfume) -> None:
        response = client.post(
            reverse("reviews:create_review", kwargs={"slug": perfume.slug}),
            {"rating": 5, "text": "Ótimo"},
        )

        assert response.status_code == 302
        assert "login" in response.url

    def test_usuario_logado_cria_review(self, client, perfume) -> None:
        user = User.objects.create_user("resenhista", password="senha123")
        client.force_login(user)

        response = client.post(
            reverse("reviews:create_review", kwargs={"slug": perfume.slug}),
            {"rating": 4, "text": "Gostei bastante"},
        )

        assert response.status_code == 302
        review = Review.objects.get(perfume=perfume, user=user)
        assert review.rating == 4
        assert review.text == "Gostei bastante"

    def test_segunda_review_do_mesmo_usuario_atualiza_em_vez_de_duplicar(self, client, perfume) -> None:
        user = User.objects.create_user("resenhista", password="senha123")
        client.force_login(user)
        url = reverse("reviews:create_review", kwargs={"slug": perfume.slug})

        client.post(url, {"rating": 2, "text": "Não curti no início"})
        client.post(url, {"rating": 5, "text": "Melhorou muito com o tempo"})

        assert Review.objects.filter(perfume=perfume, user=user).count() == 1
        review = Review.objects.get(perfume=perfume, user=user)
        assert review.rating == 5
        assert review.text == "Melhorou muito com o tempo"


class TestToggleLike:
    @pytest.fixture()
    def review(self, perfume) -> Review:
        autor = User.objects.create_user("autor", password="senha123")
        return Review.objects.create(perfume=perfume, user=autor, rating=5, text="Ótimo")

    def test_anonimo_e_redirecionado_pro_login(self, client, review) -> None:
        response = client.post(reverse("reviews:toggle_like", kwargs={"review_id": review.id}))

        assert response.status_code == 302
        assert "login" in response.url
        assert ReviewLike.objects.count() == 0

    def test_usuario_logado_curte(self, client, review) -> None:
        user = User.objects.create_user("leitor", password="senha123")
        client.force_login(user)

        client.post(reverse("reviews:toggle_like", kwargs={"review_id": review.id}))

        assert ReviewLike.objects.filter(review=review, user=user).exists()

    def test_curtir_de_novo_descurte(self, client, review) -> None:
        user = User.objects.create_user("leitor", password="senha123")
        client.force_login(user)
        url = reverse("reviews:toggle_like", kwargs={"review_id": review.id})

        client.post(url)
        client.post(url)

        assert not ReviewLike.objects.filter(review=review, user=user).exists()

    def test_pode_curtir_a_propria_review(self, client, review) -> None:
        client.force_login(review.user)

        client.post(reverse("reviews:toggle_like", kwargs={"review_id": review.id}))

        assert ReviewLike.objects.filter(review=review, user=review.user).exists()

    def test_contagem_aparece_na_pagina_do_perfume(self, client, review) -> None:
        u1 = User.objects.create_user("u1", password="senha123")
        u2 = User.objects.create_user("u2", password="senha123")
        ReviewLike.objects.create(review=review, user=u1)
        ReviewLike.objects.create(review=review, user=u2)

        response = client.get(review.perfume.get_absolute_url())

        assert "👍 2".encode() in response.content
