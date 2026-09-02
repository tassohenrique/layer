import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from catalog.models import Brand, Perfume
from reviews.models import Review, ReviewLike, ReviewUpdate

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

    def test_segunda_tentativa_de_criar_review_nao_sobrescreve_a_original(self, client, perfume) -> None:
        """A review original é imutável — reenviar create_review não faz nada (usa add_review_update pra isso)."""
        user = User.objects.create_user("resenhista", password="senha123")
        client.force_login(user)
        url = reverse("reviews:create_review", kwargs={"slug": perfume.slug})

        client.post(url, {"rating": 2, "text": "Não curti no início"})
        client.post(url, {"rating": 5, "text": "Tentando sobrescrever"})

        assert Review.objects.filter(perfume=perfume, user=user).count() == 1
        review = Review.objects.get(perfume=perfume, user=user)
        assert review.rating == 2
        assert review.text == "Não curti no início"


class TestAddReviewUpdate:
    @pytest.fixture()
    def review(self, perfume) -> Review:
        autor = User.objects.create_user("autor", password="senha123")
        return Review.objects.create(perfume=perfume, user=autor, rating=2, text="Não curti no início")

    def test_anonimo_e_redirecionado_pro_login(self, client, review) -> None:
        response = client.post(
            reverse("reviews:add_review_update", kwargs={"slug": review.perfume.slug}),
            {"rating": 5, "text": "Melhorou muito"},
        )

        assert response.status_code == 302
        assert "login" in response.url
        assert ReviewUpdate.objects.count() == 0

    def test_usuario_sem_review_recebe_404(self, client, perfume) -> None:
        user = User.objects.create_user("sem_review", password="senha123")
        client.force_login(user)

        response = client.post(
            reverse("reviews:add_review_update", kwargs={"slug": perfume.slug}),
            {"rating": 5, "text": "Não tenho review ainda"},
        )

        assert response.status_code == 404

    def test_autor_adiciona_atualizacao_preservando_a_original(self, client, review) -> None:
        client.force_login(review.user)

        client.post(
            reverse("reviews:add_review_update", kwargs={"slug": review.perfume.slug}),
            {"rating": 5, "text": "Melhorou muito com o tempo de uso"},
        )

        review.refresh_from_db()
        assert review.text == "Não curti no início"  # original intacto
        assert review.rating == 5  # rating sincronizado com a atualização mais recente
        update = ReviewUpdate.objects.get(review=review)
        assert update.rating == 5
        assert update.text == "Melhorou muito com o tempo de uso"

    def test_media_da_comunidade_usa_a_nota_mais_recente(self, client, review) -> None:
        client.force_login(review.user)

        client.post(
            reverse("reviews:add_review_update", kwargs={"slug": review.perfume.slug}),
            {"rating": 5, "text": "Melhorou"},
        )

        stats = review.perfume.rating_stats
        assert stats["average"] == 5
        assert stats["count"] == 1

    def test_varias_atualizacoes_ficam_no_historico(self, client, review) -> None:
        client.force_login(review.user)
        url = reverse("reviews:add_review_update", kwargs={"slug": review.perfume.slug})

        client.post(url, {"rating": 3, "text": "Primeira atualização"})
        client.post(url, {"rating": 4, "text": "Segunda atualização"})

        assert ReviewUpdate.objects.filter(review=review).count() == 2
        review.refresh_from_db()
        assert review.rating == 4


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


class TestReviewHistoryOnPerfumePage:
    def test_original_e_atualizacao_aparecem_na_pagina(self, client, perfume) -> None:
        autor = User.objects.create_user("autor", password="senha123")
        review = Review.objects.create(perfume=perfume, user=autor, rating=2, text="Não curti no início")
        ReviewUpdate.objects.create(review=review, rating=5, text="Melhorou muito com o tempo")

        response = client.get(perfume.get_absolute_url())

        assert b"N\xc3\xa3o curti no in\xc3\xadcio" in response.content
        assert "Melhorou muito com o tempo".encode() in response.content
        assert "Atualização em".encode("utf-8") in response.content
