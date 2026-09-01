from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Brand(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Accord(models.Model):
    """Família olfativa (ex.: amadeirado, cítrico, doce) — usada como tag do perfume."""

    key = models.SlugField(max_length=40, unique=True)
    label_pt = models.CharField(max_length=60)

    class Meta:
        ordering = ["label_pt"]

    def __str__(self) -> str:
        return self.label_pt


class Note(models.Model):
    """Nota olfativa individual (ex.: bergamota, baunilha)."""

    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Concentration(models.TextChoices):
    COLOGNE = "cologne", "Cologne"
    EDT = "edt", "EDT"
    EDP = "edp", "EDP"
    PARFUM = "parfum", "Parfum"
    EXTRAIT = "extrait", "Extrait"


class Perfume(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="perfumes")
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    launch_year = models.PositiveSmallIntegerField(null=True, blank=True)
    perfumer = models.CharField(max_length=150, blank=True)
    concentration = models.CharField(max_length=10, choices=Concentration.choices, default=Concentration.EDP)

    notes_top = models.ManyToManyField(Note, related_name="top_of", blank=True)
    notes_heart = models.ManyToManyField(Note, related_name="heart_of", blank=True)
    notes_base = models.ManyToManyField(Note, related_name="base_of", blank=True)
    accords = models.ManyToManyField(Accord, related_name="perfumes", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["brand__name", "name"]
        constraints = [
            models.UniqueConstraint(fields=["brand", "name"], name="unique_perfume_per_brand"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.brand.name})"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base_slug = slugify(f"{self.brand.name}-{self.name}")
            slug = base_slug
            i = 2
            while Perfume.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:perfume_detail", kwargs={"slug": self.slug})

    @property
    def rating_stats(self) -> dict:
        """Nota média e contagem de votos, calculadas em tempo real (dataset pequeno no MVP)."""
        from django.db.models import Avg, Count

        stats = self.reviews.aggregate(average=Avg("rating"), count=Count("id"))
        return {"average": stats["average"] or 0, "count": stats["count"] or 0}
