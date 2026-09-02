from django.conf import settings
from django.db import models


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    perfume = models.ForeignKey("catalog.Perfume", on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "perfume"], name="one_favorite_per_user_per_perfume"),
        ]

    def __str__(self) -> str:
        return f"{self.user} ♥ {self.perfume}"
