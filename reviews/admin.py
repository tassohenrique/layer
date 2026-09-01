from django.contrib import admin

from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["perfume", "user", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = ["perfume__name", "user__username"]
