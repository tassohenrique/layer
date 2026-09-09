import pytest
from django.urls import reverse

from catalog.models import Brand, Perfume

pytestmark = pytest.mark.django_db


class TestBrandListView:
    def test_lista_marcas_cadastradas(self, client) -> None:
        Brand.objects.create(name="Chanel")
        Brand.objects.create(name="Dior")

        response = client.get(reverse("catalog:brand_list"))

        assert response.status_code == 200
        assert b"Chanel" in response.content
        assert b"Dior" in response.content

    def test_busca_filtra_por_nome(self, client) -> None:
        Brand.objects.create(name="Chanel")
        Brand.objects.create(name="Dior")

        response = client.get(reverse("catalog:brand_list"), {"q": "chan"})

        assert b"Chanel" in response.content
        assert b"Dior" not in response.content

    def test_mostra_contagem_de_perfumes(self, client) -> None:
        brand = Brand.objects.create(name="Chanel")
        Perfume.objects.create(brand=brand, name="No. 5", concentration="edp")
        Perfume.objects.create(brand=brand, name="Coco", concentration="edp")

        response = client.get(reverse("catalog:brand_list"))

        assert b"2 perfumes" in response.content

    def test_acessivel_sem_login(self, client) -> None:
        response = client.get(reverse("catalog:brand_list"))
        assert response.status_code == 200


class TestBrandDetailView:
    def test_pagina_lista_perfumes_da_marca(self, client) -> None:
        chanel = Brand.objects.create(name="Chanel")
        dior = Brand.objects.create(name="Dior")
        Perfume.objects.create(brand=chanel, name="No. 5", concentration="edp")
        Perfume.objects.create(brand=dior, name="Sauvage", concentration="edt")

        response = client.get(reverse("catalog:brand_detail", kwargs={"slug": chanel.slug}))

        assert response.status_code == 200
        assert b"No. 5" in response.content
        assert b"Sauvage" not in response.content

    def test_marca_inexistente_retorna_404(self, client) -> None:
        response = client.get(reverse("catalog:brand_detail", kwargs={"slug": "nao-existe"}))
        assert response.status_code == 404
