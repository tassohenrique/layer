from django.conf import settings
from django.db import models


class Favorite(models.Model):
    """A relação de um usuário com um perfume: quero ter (padrão) ou já tenho.

    Não é um app de coleção separado de propósito — reaproveita o mesmo
    registro do "favoritar" pra guardar também a posse (`owned`), evitando
    reconstruir o conceito de coleção pessoal do app antigo como produto
    isolado (ver CLAUDE.md, seção "Já implementado além do MVP original").
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    perfume = models.ForeignKey("catalog.Perfume", on_delete=models.CASCADE, related_name="favorited_by")
    owned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "perfume"], name="one_favorite_per_user_per_perfume"),
        ]

    def __str__(self) -> str:
        return f"{self.user} {'📦' if self.owned else '♥'} {self.perfume}"
