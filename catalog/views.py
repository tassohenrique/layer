from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, render

from catalog.models import Perfume
from reviews.forms import ReviewForm


def perfume_list(request):
    perfumes = Perfume.objects.select_related("brand").annotate(
        avg_rating=Avg("reviews__rating"), review_count=Count("reviews")
    )
    return render(request, "catalog/perfume_list.html", {"perfumes": perfumes})


def perfume_detail(request, slug):
    perfume = get_object_or_404(
        Perfume.objects.select_related("brand").prefetch_related(
            "notes_top", "notes_heart", "notes_base", "accords"
        ),
        slug=slug,
    )
    perfume_reviews = perfume.reviews.select_related("user", "user__profile")
    stats = perfume.rating_stats

    user_review = None
    if request.user.is_authenticated:
        user_review = perfume_reviews.filter(user=request.user).first()

    context = {
        "perfume": perfume,
        "reviews": perfume_reviews,
        "stats": stats,
        "form": ReviewForm(instance=user_review),
        "user_review": user_review,
    }
    return render(request, "catalog/perfume_detail.html", context)
