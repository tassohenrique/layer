from django import forms

from reviews.models import Review, ReviewUpdate


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "text"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "text": forms.Textarea(attrs={"rows": 4, "placeholder": "O que você achou desse perfume?"}),
        }


class ReviewUpdateForm(forms.ModelForm):
    class Meta:
        model = ReviewUpdate
        fields = ["rating", "text"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "text": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Como está depois de mais tempo de uso?"}
            ),
        }
