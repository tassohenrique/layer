import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_profile_e_criado_automaticamente_para_novo_usuario() -> None:
    user = User.objects.create_user("novo", password="senha123")

    assert user.profile is not None
    assert user.profile.name == "novo"


class TestLogout:
    def test_post_desloga_o_usuario(self, client) -> None:
        user = User.objects.create_user("logado", password="senha123")
        client.force_login(user)

        response = client.post(reverse("accounts:logout"))

        assert response.status_code == 302
        response = client.get(reverse("accounts:profile"))
        assert response.status_code == 302  # login_required redireciona: não está mais logado

    def test_get_nao_e_permitido(self, client) -> None:
        user = User.objects.create_user("logado", password="senha123")
        client.force_login(user)

        response = client.get(reverse("accounts:logout"))

        assert response.status_code == 405
