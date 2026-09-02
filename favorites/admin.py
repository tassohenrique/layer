from django.contrib import admin

from favorites.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "perfume", "created_at"]
    search_fields = ["user__username", "perfume__name"]
