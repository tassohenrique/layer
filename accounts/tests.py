import pytest
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db


def test_profile_e_criado_automaticamente_para_novo_usuario() -> None:
    user = User.objects.create_user("novo", password="senha123")

    assert user.profile is not None
    assert user.profile.name == "novo"
