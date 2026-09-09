from django.urls import path

from catalog import views

app_name = "catalog"
urlpatterns = [
    path("", views.perfume_list, name="perfume_list"),
    path("em-alta/", views.trending, name="trending"),
    path("marcas/", views.brand_list, name="brand_list"),
    path("marcas/<slug:slug>/", views.brand_detail, name="brand_detail"),
    path("perfumes/<slug:slug>/", views.perfume_detail, name="perfume_detail"),
]
