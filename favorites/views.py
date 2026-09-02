from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Perfume
from favorites.models import Favorite


@login_required
@require_POST
def toggle_favorite(request, slug):
    """Favorita o perfume, ou desfavorita se já estiver na lista."""
    perfume = get_object_or_404(Perfume, slug=slug)
    favorite = Favorite.objects.filter(user=request.user, perfume=perfume).first()
    if favorite:
        favorite.delete()
    else:
        Favorite.objects.create(user=request.user, perfume=perfume)
    return redirect("catalog:perfume_detail", slug=perfume.slug)


@login_required
@require_POST
def toggle_owned(request, slug):
    """Marca o perfume como possuído (cria o favorito se preciso), ou desmarca sem sair da lista."""
    perfume = get_object_or_404(Perfume, slug=slug)
    favorite, created = Favorite.objects.get_or_create(user=request.user, perfume=perfume)
    favorite.owned = True if created else not favorite.owned
    favorite.save()
    return redirect("catalog:perfume_detail", slug=perfume.slug)


@login_required
def favorite_list(request):
    status = request.GET.get("status", "").strip()

    favorites = Favorite.objects.filter(user=request.user).select_related("perfume", "perfume__brand")
    if status == "owned":
        favorites = favorites.filter(owned=True)
    elif status == "wishlist":
        favorites = favorites.filter(owned=False)

    context = {"favorites": favorites, "status": status}
    return render(request, "favorites/favorite_list.html", context)
