from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from catalog.models import Perfume
from reviews.forms import ReviewForm, ReviewUpdateForm
from reviews.models import Review, ReviewLike


@login_required
@require_POST
def create_review(request, slug):
    """Cria a review do usuário pra esse perfume — só a primeira vez.

    A review original nunca é sobrescrita (1 por usuário via
    unique_together). Se o usuário já tem uma review pra esse perfume,
    esse endpoint não faz nada — atualizações depois disso passam por
    `add_review_update`, que preserva o texto/nota originais.
    """
    perfume = get_object_or_404(Perfume, slug=slug)
    if Review.objects.filter(perfume=perfume, user=request.user).exists():
        return redirect("catalog:perfume_detail", slug=perfume.slug)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.perfume = perfume
        review.user = request.user
        review.save()
    return redirect("catalog:perfume_detail", slug=perfume.slug)


@login_required
@require_POST
def add_review_update(request, slug):
    """Adiciona uma atualização à review existente do usuário, sem apagar a original."""
    perfume = get_object_or_404(Perfume, slug=slug)
    review = get_object_or_404(Review, perfume=perfume, user=request.user)

    form = ReviewUpdateForm(request.POST)
    if form.is_valid():
        update = form.save(commit=False)
        update.review = review
        update.save()
        review.rating = update.rating
        review.save(update_fields=["rating", "updated_at"])
    return redirect("catalog:perfume_detail", slug=perfume.slug)


@login_required
@require_POST
def toggle_like(request, review_id):
    """Curte a review, ou descurte se o usuário já tiver curtido."""
    review = get_object_or_404(Review, pk=review_id)
    like = ReviewLike.objects.filter(review=review, user=request.user).first()
    if like:
        like.delete()
    else:
        ReviewLike.objects.create(review=review, user=request.user)
    return redirect("catalog:perfume_detail", slug=review.perfume.slug)
