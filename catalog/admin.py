from django.contrib import admin

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
    list_display = ["name", "brand", "concentration", "launch_year"]
    list_filter = ["concentration", "accords", "brand"]
    search_fields = ["name", "brand__name"]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ["notes_top", "notes_heart", "notes_base", "accords"]
