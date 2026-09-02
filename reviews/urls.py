from django.urls import path

from reviews import views

app_name = "reviews"
urlpatterns = [
    path("perfumes/<slug:slug>/review/", views.create_review, name="create_review"),
    path("reviews/<int:review_id>/like/", views.toggle_like, name="toggle_like"),
]
