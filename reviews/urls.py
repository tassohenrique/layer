from django.urls import path

from reviews import views

app_name = "reviews"
urlpatterns = [
    path("perfumes/<slug:slug>/review/", views.create_review, name="create_review"),
    path("perfumes/<slug:slug>/review/update/", views.add_review_update, name="add_review_update"),
    path("reviews/<int:review_id>/like/", views.toggle_like, name="toggle_like"),
]
