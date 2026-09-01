import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from catalog.models import Brand, Perfume
from reviews.models import Review

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
