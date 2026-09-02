from django.contrib import admin

from reviews.models import Review, ReviewLike, ReviewUpdate


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["perfume", "user", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = ["perfume__name", "user__username"]


@admin.register(ReviewUpdate)
class ReviewUpdateAdmin(admin.ModelAdmin):
    list_display = ["review", "rating", "created_at"]


@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ["review", "user", "created_at"]
