from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render

from catalog.models import Accord, Perfume
from favorites.models import Favorite
from reviews.forms import ReviewForm, ReviewUpdateForm
from reviews.models import ReviewLike


def perfume_list(request):
    query = request.GET.get("q", "").strip()
    accord_key = request.GET.get("accord", "").strip()

    perfumes = Perfume.objects.select_related("brand").annotate(
        avg_rating=Avg("reviews__rating"), review_count=Count("reviews")
    )

    if query:
        perfumes = perfumes.filter(
            Q(name__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(notes_top__name__icontains=query)
            | Q(notes_heart__name__icontains=query)
            | Q(notes_base__name__icontains=query)
        ).distinct()

    if accord_key:
        perfumes = perfumes.filter(accords__key=accord_key).distinct()

    context = {
        "perfumes": perfumes,
        "query": query,
        "selected_accord": accord_key,
        "accords": Accord.objects.all(),
        "has_filters": bool(query or accord_key),
    }
    return render(request, "catalog/perfume_list.html", context)


def perfume_detail(request, slug):
    perfume = get_object_or_404(
        Perfume.objects.select_related("brand").prefetch_related(
            "notes_top", "notes_heart", "notes_base", "accords"
        ),
        slug=slug,
    )
    perfume_reviews = (
        perfume.reviews.select_related("user", "user__profile")
        .prefetch_related("updates")
        .annotate(like_count=Count("likes"))
    )
    stats = perfume.rating_stats

    user_review = None
    is_favorited = False
    is_owned = False
    liked_review_ids: set[int] = set()
    if request.user.is_authenticated:
        user_review = perfume_reviews.filter(user=request.user).first()
        user_favorite = Favorite.objects.filter(user=request.user, perfume=perfume).first()
        is_favorited = user_favorite is not None
        is_owned = bool(user_favorite and user_favorite.owned)
        liked_review_ids = set(
            ReviewLike.objects.filter(user=request.user, review__perfume=perfume).values_list(
                "review_id", flat=True
            )
        )

    context = {
        "perfume": perfume,
        "reviews": perfume_reviews,
        "stats": stats,
        "form": ReviewForm(),
        "update_form": ReviewUpdateForm(),
        "user_review": user_review,
        "is_favorited": is_favorited,
        "is_owned": is_owned,
        "favorite_count": perfume.favorited_by.count(),
        "owned_count": perfume.favorited_by.filter(owned=True).count(),
        "liked_review_ids": liked_review_ids,
    }
    return render(request, "catalog/perfume_detail.html", context)
