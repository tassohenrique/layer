from django.urls import path

from favorites import views

app_name = "favorites"
urlpatterns = [
    path("favoritos/", views.favorite_list, name="favorite_list"),
    path("perfumes/<slug:slug>/favorite/", views.toggle_favorite, name="toggle_favorite"),
]
