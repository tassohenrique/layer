from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from catalog.models import Perfume
from reviews.forms import ReviewForm
from reviews.models import Review, ReviewLike


@login_required
@require_POST
def create_review(request, slug):
    """Cria a review do usuário pra esse perfume, ou atualiza a existente (1 por usuário)."""
    perfume = get_object_or_404(Perfume, slug=slug)
    instance = Review.objects.filter(perfume=perfume, user=request.user).first()
    form = ReviewForm(request.POST, instance=instance)
    if form.is_valid():
        review = form.save(commit=False)
        review.perfume = perfume
        review.user = request.user
        review.save()
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
