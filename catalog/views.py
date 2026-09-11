from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render

from catalog.compare import MAX_COMPARE, parse_compare_slugs
from catalog.models import Accord, Brand, Perfume
from catalog.recommendations import similar_perfumes
from catalog.trending import DEFAULT_WINDOW_DAYS, trending_perfumes
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


def trending(request):
    context = {
        "perfumes": trending_perfumes(),
        "window_days": DEFAULT_WINDOW_DAYS,
    }
    return render(request, "catalog/trending.html", context)


def brand_list(request):
    query = request.GET.get("q", "").strip()

    brands = Brand.objects.annotate(perfume_count=Count("perfumes"))

    if query:
        brands = brands.filter(name__icontains=query)

    context = {
        "brands": brands,
        "query": query,
    }
    return render(request, "catalog/brand_list.html", context)


def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    perfumes = (
        Perfume.objects.filter(brand=brand)
        .select_related("brand")
        .annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews"))
    )

    context = {
        "brand": brand,
        "perfumes": perfumes,
    }
    return render(request, "catalog/brand_detail.html", context)


def compare(request):
    slugs = parse_compare_slugs(request.GET)

    perfumes_by_slug = {
        perfume.slug: perfume
        for perfume in Perfume.objects.filter(slug__in=slugs)
        .select_related("brand")
        .prefetch_related("notes_top", "notes_heart", "notes_base", "accords")
    }
    # reconstrói na ordem dos slugs (query não garante ordem de um filter __in)
    perfumes = [perfumes_by_slug[s] for s in slugs if s in perfumes_by_slug]

    context = {
        "perfumes": perfumes,
        "stats": {perfume.slug: perfume.rating_stats for perfume in perfumes},
        "selected_slugs": slugs,
        "all_perfumes": Perfume.objects.select_related("brand"),
        "max_compare": MAX_COMPARE,
        "can_add_more": len(perfumes) < MAX_COMPARE,
    }
    return render(request, "catalog/compare.html", context)


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
        "similar_perfumes": similar_perfumes(perfume),
    }
    return render(request, "catalog/perfume_detail.html", context)
