from django.urls import path

from catalog import views

app_name = "catalog"
urlpatterns = [
    path("", views.perfume_list, name="perfume_list"),
    path("perfumes/<slug:slug>/", views.perfume_detail, name="perfume_detail"),
]
