import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from catalog.models import Brand, Perfume
from favorites.models import Favorite

pytestmark = pytest.mark.django_db


@pytest.fixture()
def perfume() -> Perfume:
    brand = Brand.objects.create(name="Marca Teste")
    return Perfume.objects.create(brand=brand, name="Perfume Teste", concentration="edp")


class TestToggleFavorite:
    def test_anonimo_e_redirecionado_pro_login(self, client, perfume) -> None:
        response = client.post(reverse("favorites:toggle_favorite", kwargs={"slug": perfume.slug}))

        assert response.status_code == 302
        assert "login" in response.url
        assert Favorite.objects.count() == 0

    def test_usuario_logado_favorita(self, client, perfume) -> None:
        user = User.objects.create_user("fã", password="senha123")
        client.force_login(user)

        response = client.post(reverse("favorites:toggle_favorite", kwargs={"slug": perfume.slug}))

        assert response.status_code == 302
        assert Favorite.objects.filter(user=user, perfume=perfume).exists()

    def test_favoritar_de_novo_desfavorita(self, client, perfume) -> None:
        user = User.objects.create_user("fã", password="senha123")
        client.force_login(user)
        url = reverse("favorites:toggle_favorite", kwargs={"slug": perfume.slug})

        client.post(url)
        client.post(url)

        assert not Favorite.objects.filter(user=user, perfume=perfume).exists()

    def test_favoritos_sao_por_usuario(self, client, perfume) -> None:
        u1 = User.objects.create_user("u1", password="senha123")
        u2 = User.objects.create_user("u2", password="senha123")
        Favorite.objects.create(user=u1, perfume=perfume)

        client.force_login(u2)
        response = client.get(perfume.get_absolute_url())

        assert b"\xe2\x99\xa1 Favoritar" in response.content  # ainda não favoritado pelo u2


class TestFavoriteList:
    def test_lista_exige_login(self, client) -> None:
        response = client.get(reverse("favorites:favorite_list"))
        assert response.status_code == 302

    def test_lista_mostra_so_os_favoritos_do_usuario(self, client, perfume) -> None:
        outro_perfume = Perfume.objects.create(
            brand=Brand.objects.create(name="Outra Marca"), name="Outro Perfume", concentration="edt"
        )
        u1 = User.objects.create_user("u1", password="senha123")
        u2 = User.objects.create_user("u2", password="senha123")
        Favorite.objects.create(user=u1, perfume=perfume)
        Favorite.objects.create(user=u2, perfume=outro_perfume)

        client.force_login(u1)
        response = client.get(reverse("favorites:favorite_list"))

        assert b"Perfume Teste" in response.content
        assert b"Outro Perfume" not in response.content
