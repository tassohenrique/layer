from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    perfume = models.ForeignKey("catalog.Perfume", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")

    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["perfume", "user"], name="one_review_per_user_per_perfume"),
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.perfume} ({self.rating})"


class ReviewUpdate(models.Model):
    """Atualização de uma review depois de mais tempo de uso do perfume.

    A review original (`Review.text`/`Review.rating`) nunca é sobrescrita —
    reenviar o formulário de review cria um registro aqui em vez de editar
    a original, preservando o histórico. `Review.rating` é sincronizado
    pra sempre refletir a nota mais recente (a original, se não houver
    atualização, ou a da última atualização), porque é o que
    `Perfume.rating_stats` usa pra calcular a média da comunidade — a
    média deve refletir a opinião atual de cada pessoa, não a média das
    suas próprias notas ao longo do tempo.
    """

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="updates")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Atualização de {self.review} em {self.created_at:%d/%m/%Y}"


class ReviewLike(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["review", "user"], name="one_like_per_user_per_review"),
        ]

    def __str__(self) -> str:
        return f"{self.user} curtiu a review de {self.review.user} em {self.review.perfume}"
