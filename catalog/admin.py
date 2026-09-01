from django.contrib import admin
from django.utils.html import format_html

from catalog.models import Accord, Brand, Note, Perfume


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Accord)
class AccordAdmin(admin.ModelAdmin):
    list_display = ["label_pt", "key"]
    prepopulated_fields = {"key": ("label_pt",)}


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Perfume)
class PerfumeAdmin(admin.ModelAdmin):
    list_display = ["thumbnail", "name", "brand", "concentration", "launch_year"]
    list_filter = ["concentration", "accords", "brand"]
    search_fields = ["name", "brand__name"]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ["notes_top", "notes_heart", "notes_base", "accords"]
    readonly_fields = ["image_preview"]

    @admin.display(description="")
    def thumbnail(self, obj: Perfume) -> str:
        if not obj.image:
            return "—"
        return format_html('<img src="{}" style="width:32px; height:32px; object-fit:cover; border-radius:4px;">', obj.image.url)

    @admin.display(description="Pré-visualização")
    def image_preview(self, obj: Perfume) -> str:
        if not obj.image:
            return "Sem imagem ainda"
        return format_html('<img src="{}" style="max-width:200px; border-radius:8px;">', obj.image.url)
